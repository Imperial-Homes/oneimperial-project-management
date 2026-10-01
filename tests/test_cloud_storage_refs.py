"""Unit tests for resolving and presigning stored Spaces file references.

Pure tests: no database and no network (presigning is a local computation).
"""

import io
from uuid import uuid4

import pytest
from app.config import settings
from app.core import cloud_storage as cloud_storage_module
from app.core.cloud_storage import CloudStorage
from fastapi import UploadFile

BUCKET = "oneimperial-storage"
KEY = "project/site-visits/2026/10/0b8a7c1e-1234-4c3b-9a55-6f6e2d2b9f10.jpg"


@pytest.fixture
def storage(monkeypatch) -> CloudStorage:
    """CloudStorage configured with dummy credentials (signing needs no network)."""
    monkeypatch.setattr(settings, "DO_SPACES_KEY", "DUMMYACCESSKEY000000")
    monkeypatch.setattr(settings, "DO_SPACES_SECRET", "dummy-secret-key-for-unit-tests")
    monkeypatch.setattr(settings, "DO_SPACES_BUCKET", BUCKET)
    monkeypatch.setattr(settings, "DO_SPACES_REGION", "lon1")
    monkeypatch.setattr(settings, "DO_SPACES_ENDPOINT", "https://lon1.digitaloceanspaces.com")
    return CloudStorage()


@pytest.fixture
def global_storage(storage: CloudStorage, monkeypatch) -> CloudStorage:
    """Point the module-level cloud_storage used by schemas and endpoints at the dummy client."""
    monkeypatch.setattr(cloud_storage_module.cloud_storage, "client", storage.client)
    monkeypatch.setattr(cloud_storage_module.cloud_storage, "bucket_name", BUCKET)
    return cloud_storage_module.cloud_storage


def _is_signed(url: str | None) -> bool:
    return bool(url) and ("X-Amz-Signature=" in url or "Signature=" in url)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Bare key (must have a folder prefix)
        (KEY, KEY),
        # Plain filename and absolute local paths are not keys
        ("report.pdf", None),
        (f"/{KEY}", None),
        ("/app/storage/report.pdf", None),
        # CDN URL (virtual-host style)
        (f"https://{BUCKET}.lon1.cdn.digitaloceanspaces.com/{KEY}", KEY),
        # Origin URL (virtual-host style)
        (f"https://{BUCKET}.lon1.digitaloceanspaces.com/{KEY}", KEY),
        # Path-style URL
        (f"https://lon1.digitaloceanspaces.com/{BUCKET}/{KEY}", KEY),
        # Stale presigned URL: query string is dropped
        (
            f"https://{BUCKET}.lon1.digitaloceanspaces.com/project/progress-reports/a.pdf"
            "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&X-Amz-Signature=deadbeef",
            "project/progress-reports/a.pdf",
        ),
        # Percent-encoded key is decoded
        (
            f"https://{BUCKET}.lon1.cdn.digitaloceanspaces.com/project/site-visits/Site%20Photo%20%281%29.jpg",
            "project/site-visits/Site Photo (1).jpg",
        ),
        # Foreign hosts
        ("https://example.com/project/site-visits/file.jpg", None),
        ("https://other-bucket.lon1.digitaloceanspaces.com/project/file.pdf", None),
        ("https://lon1.digitaloceanspaces.com/other-bucket/project/file.pdf", None),
        # Empty
        ("", None),
        (None, None),
    ],
)
def test_key_from_reference(storage: CloudStorage, value, expected):
    assert storage.key_from_reference(value) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    [
        KEY,
        f"https://{BUCKET}.lon1.cdn.digitaloceanspaces.com/{KEY}",
        f"https://{BUCKET}.lon1.digitaloceanspaces.com/{KEY}",
        f"https://lon1.digitaloceanspaces.com/{BUCKET}/{KEY}",
        f"https://{BUCKET}.lon1.digitaloceanspaces.com/{KEY}?X-Amz-Expires=3600&X-Amz-Signature=deadbeef",
    ],
)
def test_presign_stored_signs_our_references(storage: CloudStorage, value):
    signed = storage.presign_stored(value)

    assert _is_signed(signed)
    assert "deadbeef" not in signed
    # The signed URL resolves back to the same object, so re-signing is stable
    assert storage.key_from_reference(signed) == KEY


@pytest.mark.unit
@pytest.mark.parametrize("value", ["https://example.com/project/file.pdf", "report.pdf", "/app/x.pdf", "", None])
def test_presign_stored_leaves_foreign_values_unchanged(storage: CloudStorage, value):
    assert storage.presign_stored(value) == value


@pytest.mark.unit
def test_presign_stored_without_client_returns_value(storage: CloudStorage):
    storage.client = None
    assert storage.presign_stored(KEY) == KEY


@pytest.mark.unit
def test_response_schemas_sign_file_urls_without_mutating(global_storage: CloudStorage):
    """Response schemas sign file URLs on serialization but keep the stored value."""
    from app.schemas.handover_pack import HandoverPackResponse
    from app.schemas.progress_report import ProgressReportResponse
    from app.schemas.site_visit import SiteVisitResponse

    cdn_url = f"https://{BUCKET}.lon1.cdn.digitaloceanspaces.com/{KEY}"
    common = {"id": str(uuid4()), "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}

    visit = SiteVisitResponse.model_validate(
        {
            **common,
            "visit_id": "SV-2026-0001",
            "project_name": "Test",
            "site_location": "Accra",
            "visit_date": "2026-01-01T00:00:00",
            "visit_purpose": "Inspection",
            "status": "completed",
            "logged_by": None,
            "logged_by_id": None,
            "photos_url": cdn_url,
            "report_url": "https://example.com/report.pdf",
        }
    )
    report = ProgressReportResponse.model_validate(
        {
            **common,
            "report_id": "PR-2026-0001",
            "report_title": "Test",
            "report_date": "2026-01-01T00:00:00",
            "status": "draft",
            "compiled_by": None,
            "compiled_by_id": None,
            "attachment_url": KEY,
        }
    )
    handover = HandoverPackResponse.model_validate(
        {
            **common,
            "handover_id": "HP-2026-0001",
            "property_name": "Test",
            "client_name": "Client",
            "is_active": True,
            "letter_to_client_url": "https://lon1.digitaloceanspaces.com/oneimperial-storage/crm/legal-documents/a.pdf",
            "handover_pack_url": None,
        }
    )

    visit_json = visit.model_dump(mode="json")
    report_json = report.model_dump(mode="json")
    handover_json = handover.model_dump(mode="json")

    assert _is_signed(visit_json["photos_url"])
    assert visit_json["report_url"] == "https://example.com/report.pdf"
    assert _is_signed(report_json["attachment_url"])
    assert _is_signed(handover_json["letter_to_client_url"])
    assert handover_json["handover_pack_url"] is None

    # Stored values are untouched
    assert visit.photos_url == cdn_url
    assert report.attachment_url == KEY


@pytest.mark.unit
@pytest.mark.parametrize(
    ("module_name", "endpoint_name", "prefix"),
    [
        ("app.api.site_visits", "upload_site_visit_file", "project/site-visits/"),
        ("app.api.progress_reports", "upload_progress_report_file", "project/progress-reports/"),
    ],
)
async def test_upload_endpoints_return_presigned_url_and_key(
    global_storage: CloudStorage, monkeypatch, module_name, endpoint_name, prefix
):
    import importlib

    module = importlib.import_module(module_name)
    uploaded = {}

    def fake_upload(file_content, file_path, content_type=None):
        uploaded["key"] = file_path
        return f"https://{BUCKET}.lon1.cdn.digitaloceanspaces.com/{file_path}"

    monkeypatch.setattr(global_storage, "upload_file", fake_upload)

    file = UploadFile(file=io.BytesIO(b"data"), filename="photo.jpg")
    result = await getattr(module, endpoint_name)(file=file, current_user=uuid4())

    assert result["key"] == uploaded["key"]
    assert result["key"].startswith(prefix)
    assert result["file_name"] == "photo.jpg"
    assert _is_signed(result["url"])
    assert global_storage.key_from_reference(result["url"]) == result["key"]
    # The client may store this URL in a 500-char column
    assert len(result["url"]) <= 500


@pytest.mark.unit
def test_request_schemas_normalize_our_urls_to_keys(global_storage: CloudStorage):
    """Create/update schemas store bare keys, even for signed URLs longer than max_length."""
    from app.schemas.handover_pack import HandoverPackCreate, HandoverPackUpdate
    from app.schemas.progress_report import ProgressReportCreate, ProgressReportUpdate
    from app.schemas.site_visit import SiteVisitCreate, SiteVisitUpdate

    signed = global_storage.presign_stored(KEY)
    cdn_url = f"https://{BUCKET}.lon1.cdn.digitaloceanspaces.com/{KEY}"
    foreign = "https://example.com/project/file.pdf"
    assert len(signed) > 300

    report = ProgressReportCreate(report_title="t", report_date="2026-01-01T00:00:00", attachment_url=signed)
    assert report.attachment_url == KEY
    assert ProgressReportUpdate(attachment_url=cdn_url).attachment_url == KEY
    assert ProgressReportUpdate(attachment_url=foreign).attachment_url == foreign
    assert ProgressReportUpdate(attachment_url=None).attachment_url is None

    visit = SiteVisitCreate(
        project_name="p",
        site_location="s",
        visit_date="2026-01-01T00:00:00",
        visit_purpose="x",
        photos_url=signed,
        report_url=foreign,
    )
    assert visit.photos_url == KEY
    assert visit.report_url == foreign
    update = SiteVisitUpdate(photos_url=cdn_url, report_url=KEY)
    assert (update.photos_url, update.report_url) == (KEY, KEY)

    handover = HandoverPackCreate(property_name="p", client_name="c", letter_to_client_url=signed)
    assert handover.letter_to_client_url == KEY
    assert handover.model_dump()["letter_to_client_url"] == KEY
    assert HandoverPackUpdate(handover_pack_url=foreign).handover_pack_url == foreign


@pytest.mark.unit
def test_list_response_survives_fastapi_round_trip_with_long_key(global_storage: CloudStorage):
    """FastAPI dumps list responses (signing them) and re-validates; signed URLs must not hit max_length."""
    from app.schemas.progress_report import ProgressReportList

    long_key = "project/progress-reports/" + "a" * 200 + ".pdf"
    item = {
        "id": str(uuid4()),
        "report_id": "PR-2026-0001",
        "report_title": "Test",
        "report_date": "2026-01-01T00:00:00",
        "status": "draft",
        "compiled_by": None,
        "compiled_by_id": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "attachment_url": long_key,
    }
    listing = ProgressReportList(items=[item], total=1, page=1, page_size=50, pages=1)

    dumped = listing.model_dump(by_alias=True)
    assert len(dumped["items"][0]["attachment_url"]) > 500

    revalidated = ProgressReportList.model_validate(dumped)
    assert _is_signed(revalidated.model_dump(mode="json")["items"][0]["attachment_url"])
