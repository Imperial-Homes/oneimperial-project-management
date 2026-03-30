import asyncio
import random
import uuid
from datetime import date, timedelta

from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.incident import IncidentSeverity, IncidentStatus, IncidentType, ProjectIncident
from app.models.payment import CertificateStatus, CertificateType, PaymentCertificate
from app.models.project import Project, ProjectPhase
from app.models.resource import Resource, ResourceAssignment
from app.models.schedule import Milestone
from app.models.task import Task
from app.models.timeline import ProjectProgress
from app.models.variation import ProjectVariation, VariationStatus, VariationType

# Constants
CURRENCY = "GHS"

# Mock IDs for external references
CLIENT_IDS = [uuid.uuid4() for _ in range(5)]
MANAGER_IDS = [uuid.uuid4() for _ in range(5)]

PROJECTS_DATA = [
    {
        "name": "Cantonments Luxury Villa",
        "type": "Construction",
        "location": "Accra",
        "budget": 2500000,
        "status": "active",
        "priority": "high",
    },
    {
        "name": "Kumasi Office Complex",
        "type": "Construction",
        "location": "Kumasi",
        "budget": 4800000,
        "status": "active",
        "priority": "critical",
    },
    {
        "name": "East Legon Townhouses",
        "type": "Construction",
        "location": "Accra",
        "budget": 3200000,
        "status": "planning",
        "priority": "medium",
    },
    {
        "name": "Airport Hills Renovation",
        "type": "Renovation",
        "location": "Accra",
        "budget": 850000,
        "status": "active",
        "priority": "high",
    },
    {
        "name": "Tema Industrial Park",
        "type": "Construction",
        "location": "Tema",
        "budget": 6500000,
        "status": "on_hold",
        "priority": "medium",
    },
    {
        "name": "Spintex Road Apartments",
        "type": "Construction",
        "location": "Accra",
        "budget": 1800000,
        "status": "completed",
        "priority": "low",
    },
    {
        "name": "Trasacco Valley Extension",
        "type": "Landscaping",
        "location": "Accra",
        "budget": 950000,
        "status": "active",
        "priority": "medium",
    },
    {
        "name": "Takoradi Harbour Offices",
        "type": "Interior Design",
        "location": "Takoradi",
        "budget": 1200000,
        "status": "active",
        "priority": "high",
    },
]

RESOURCES = [
    {"name": "Kwame Mensah", "type": "human", "code": "RES-001", "cost": 55},
    {"name": "Ama Boateng", "type": "human", "code": "RES-002", "cost": 65},
    {"name": "Daniel Asante", "type": "human", "code": "RES-003", "cost": 48},
    {"name": "Excavator X200", "type": "equipment", "code": "EQP-001", "cost": 500},
    {"name": "Concrete Mixer", "type": "equipment", "code": "EQP-002", "cost": 150},
    {"name": "Tower Crane TC-5", "type": "equipment", "code": "EQP-003", "cost": 800},
    {"name": "Cement (Bags)", "type": "material", "code": "MAT-001", "cost": 50},
    {"name": "Steel Rods (16mm)", "type": "material", "code": "MAT-002", "cost": 4500},
]

PHASES = [
    {"name": "Planning & Design", "desc": "Architectural designs, permits, and approvals"},
    {"name": "Foundation", "desc": "Site prep, excavation, and foundation work"},
    {"name": "Superstructure", "desc": "Columns, beams, walls, and roofing"},
    {"name": "MEP Installation", "desc": "Mechanical, Electrical, and Plumbing systems"},
    {"name": "Finishing & Handover", "desc": "Plastering, painting, tiling, and final inspection"},
]


async def clear_old_data(session):
    """Clear existing project data for a clean seed."""
    print("Clearing existing project data...")
    tables = [
        "project_progress",
        "payment_certificates",
        "project_incidents",
        "project_variations",
        "resource_assignments",
        "task_dependencies",
        "milestones",
        "tasks",
        "project_phases",
        "projects",
        "resources",
    ]
    for table in tables:
        try:
            await session.execute(text(f"DELETE FROM {table}"))
        except Exception as e:
            print(f"  Could not clear {table}: {e}")
    await session.flush()
    print("Old data cleared.")


async def seed_resources(session):
    print("Seeding Resources...")
    created_resources = []

    for res_data in RESOURCES:
        new_res = Resource(
            resource_code=res_data["code"],
            name=res_data["name"],
            resource_type=res_data["type"],
            description=f"Standard {res_data['type']} resource",
            cost_per_hour=res_data["cost"] if res_data["type"] != "material" else None,
            cost_per_unit=res_data["cost"] if res_data["type"] == "material" else None,
            currency=CURRENCY,
            availability_status="available",
            is_active=True,
        )
        session.add(new_res)
        created_resources.append(new_res)

    await session.flush()
    print(f"Added {len(created_resources)} resources.")
    return created_resources


async def seed_projects(session, resources):
    print("Seeding Projects...")

    projects = []
    for i, p_data in enumerate(PROJECTS_DATA):
        start_offset = random.randint(0, 180)
        start_date = date.today() - timedelta(days=start_offset)
        duration = random.randint(180, 730)
        target_end_date = start_date + timedelta(days=duration)

        completion = 0
        if p_data["status"] == "completed":
            completion = 100
        elif p_data["status"] == "active":
            completion = random.randint(15, 75)
        elif p_data["status"] == "on_hold":
            completion = random.randint(5, 30)

        project = Project(
            project_code=f"PRJ-{2026}-{1001 + i}",
            name=p_data["name"],
            description=f"{p_data['type']} project managed by Imperial Homes in {p_data['location']}.",
            project_type=p_data["type"],
            client_id=random.choice(CLIENT_IDS),
            start_date=start_date,
            target_end_date=target_end_date,
            status=p_data["status"],
            priority=p_data["priority"],
            budget=p_data["budget"],
            currency=CURRENCY,
            manager_id=random.choice(MANAGER_IDS),
            location=p_data["location"],
            is_active=True,
        )
        session.add(project)
        await session.flush()
        projects.append(project)
        print(f"  Added Project: {project.name} ({project.project_code})")

        # --- PHASES ---
        created_phases = []
        for idx, ph_data in enumerate(PHASES):
            phase_start = start_date + timedelta(days=idx * 45)
            phase_end = phase_start + timedelta(days=40)

            if p_data["status"] == "completed":
                ph_status = "completed"
                ph_completion = 100
            elif p_data["status"] == "active":
                if idx == 0:
                    ph_status = "completed"
                    ph_completion = 100
                elif idx == 1:
                    ph_status = "in_progress"
                    ph_completion = random.randint(40, 80)
                else:
                    ph_status = "pending"
                    ph_completion = 0
            else:
                ph_status = "pending"
                ph_completion = 0

            phase = ProjectPhase(
                project_id=project.id,
                name=ph_data["name"],
                description=ph_data["desc"],
                sequence_number=idx + 1,
                start_date=phase_start,
                end_date=phase_end,
                status=ph_status,
                completion_percentage=ph_completion,
            )
            session.add(phase)
            await session.flush()
            created_phases.append(phase)

            # --- TASKS per Phase ---
            task_names = [
                f"{ph_data['name']} - Planning",
                f"{ph_data['name']} - Execution",
                f"{ph_data['name']} - Review & QA",
            ]
            for t_idx, t_name in enumerate(task_names):
                task = Task(
                    project_id=project.id,
                    phase_id=phase.id,
                    task_code=f"TSK-{project.project_code[-4:]}-{phase.sequence_number}-{t_idx + 1}",
                    name=t_name,
                    description=f"Detailed work item for {phase.name}",
                    start_date=phase_start + timedelta(days=t_idx * 10),
                    due_date=phase_start + timedelta(days=(t_idx + 1) * 10),
                    estimated_hours=random.randint(20, 120),
                    status=ph_status if ph_status != "pending" else "todo",
                    priority="medium",
                    completion_percentage=ph_completion,
                )
                session.add(task)
                await session.flush()

                # Assign Resource
                if resources:
                    assign = ResourceAssignment(
                        resource_id=random.choice(resources).id,
                        task_id=task.id,
                        project_id=project.id,
                        start_date=task.start_date,
                        end_date=task.due_date,
                        allocation_percentage=100,
                        status="active",
                    )
                    session.add(assign)

        # --- MILESTONES ---
        milestone_names = [
            "Design Approval",
            "Foundation Complete",
            "Structure Topped Out",
            "MEP Certified",
            "Final Handover",
        ]
        for m_idx, m_name in enumerate(milestone_names):
            milestone = Milestone(
                project_id=project.id,
                name=m_name,
                description=f"Key milestone: {m_name}",
                due_date=start_date + timedelta(days=(m_idx + 1) * 50),
                status="achieved"
                if p_data["status"] == "completed"
                else ("achieved" if m_idx == 0 and p_data["status"] == "active" else "pending"),
                priority="high",
            )
            session.add(milestone)

        # --- VARIATIONS (for active projects) ---
        if p_data["status"] == "active":
            var = ProjectVariation(
                variation_number=f"VAR-{project.project_code[-4:]}-001",
                project_id=project.id,
                title="Client requested design change",
                description="Modification to floor plan layout per client request",
                variation_type=VariationType.CLIENT_REQUEST,
                status=VariationStatus.APPROVED,
                requested_by=project.client_id,
                variation_amount=random.randint(10000, 50000),
                new_total_amount=float(project.budget) + random.randint(10000, 50000),
                justification="Client preference",
                impact_on_timeline=random.randint(3, 14),
            )
            session.add(var)

        # --- INCIDENTS ---
        if random.random() > 0.5:
            inc = ProjectIncident(
                incident_number=f"INC-{project.project_code[-4:]}-001",
                project_id=project.id,
                incident_type=random.choice(list(IncidentType)),
                severity=random.choice(list(IncidentSeverity)),
                status=random.choice([IncidentStatus.RESOLVED, IncidentStatus.INVESTIGATING]),
                title="Safety incident reported on site",
                description="Incident occurred during construction activities",
                incident_date=date.today() - timedelta(days=random.randint(5, 60)),
                reported_date=date.today() - timedelta(days=random.randint(1, 5)),
                location=f"Site {p_data['location']}, Zone {random.randint(1, 5)}",
                preventive_measures="Safety briefing conducted, area secured",
            )
            session.add(inc)

        # --- PAYMENT CERTIFICATE ---
        cert = PaymentCertificate(
            certificate_number=f"CRT-{project.project_code[-4:]}-01",
            project_id=project.id,
            certificate_date=date.today() - timedelta(days=random.randint(5, 30)),
            certificate_type=CertificateType.INTERIM,
            status=CertificateStatus.APPROVED,
            gross_amount=random.randint(50000, 200000),
            current_amount=random.randint(45000, 190000),
            net_amount=random.randint(40000, 180000),
            description="Payment for phase completion works",
        )
        session.add(cert)

        # --- PROJECT PROGRESS ---
        prog = ProjectProgress(
            project_id=project.id,
            overall_progress=completion,
            physical_progress=completion + random.randint(-5, 5),
            financial_progress=random.randint(max(0, completion - 15), min(100, completion + 15)),
            schedule_variance=random.randint(-10, 10),
            cost_variance=random.randint(-50000, 50000),
        )
        session.add(prog)

    return projects


async def main():
    async with AsyncSessionLocal() as session:
        try:
            # Clear old data first
            await clear_old_data(session)
            await session.commit()

            # Seed fresh data
            async with AsyncSessionLocal() as session2:
                resources = await seed_resources(session2)
                projects = await seed_projects(session2, resources)
                await session2.commit()

            print("\nProject Management Seeding completed successfully!")
            print(f"Created {len(PROJECTS_DATA)} projects with phases, tasks, milestones, and more.")
        except Exception as e:
            print(f"Error seeding project management data: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
