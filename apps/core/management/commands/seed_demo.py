"""Crea datos de demostración: usuarios con cada rol, proyectos, sprints, tareas, Gantt y presupuesto.

Solo para desarrollo local. Uso: python manage.py seed_demo
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.backlog import services as backlog
from apps.board.models import BoardColumn
from apps.budget import services as budget
from apps.projects import services as projects
from apps.projects.models import ProjectMember
from apps.sprints import services as sprints

PASSWORD = "Demo12345!"
USERS = [
    ("ana@demo.com", "Ana Product Owner"),
    ("luis@demo.com", "Luis Scrum Master"),
    ("marta@demo.com", "Marta Desarrollo"),
    ("pedro@demo.com", "Pedro Desarrollo"),
]


class Command(BaseCommand):
    help = "Crea datos de demostración (solo desarrollo local)."

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(email="ana@demo.com").exists():
            self.enrich()
            self.stdout.write("Los datos de demostración ya existían: se completaron empresas, fechas, objetivos y comentarios.")
            return
        ana, luis, marta, pedro = (User.objects.create_user(e, PASSWORD, name=n) for e, n in USERS)
        today = datetime.date.today()
        d = lambda n: today + datetime.timedelta(days=n)  # noqa: E731

        # ------------------------------------------------ Proyecto 1: completo
        p = projects.create_project(ana, "Rediseño del sitio web", "Nuevo sitio corporativo y migración del contenido.")
        projects.add_member(p, luis.email, ProjectMember.SCRUM_MASTER)
        projects.add_member(p, marta.email, ProjectMember.DEVELOPER)
        projects.add_member(p, pedro.email, ProjectMember.DEVELOPER)
        col = {c.name: c for c in BoardColumn.objects.filter(project=p)}

        backlog.create_milestone(p, "Lanzamiento del sitio", d(20))
        backlog.create_milestone(p, "Revisión con dirección", d(5))

        story_home = backlog.create_task(p, title="Como visitante quiero una página de inicio clara", kind="story")
        story_blog = backlog.create_task(p, title="Como lector quiero encontrar los artículos", kind="story")

        def task(title, assignee=None, points=3, **kw):
            return backlog.create_task(p, title=title, assignee=assignee, estimate_points=points, **kw)

        # Sprint 1 (cerrado, con historial)
        t1 = task("Definir guía de estilo", marta, 2, parent=story_home)
        t2 = task("Maquetar página de inicio", marta, 5, parent=story_home)
        t3 = task("Elegir tipografías", pedro, 1)
        t4 = task("Auditar contenido actual", pedro, 3)
        s1 = sprints.create_sprint(p, "Sprint 1", "Base visual del sitio", d(-21), d(-8))
        for t in (t1, t2, t3, t4):
            backlog.assign_sprint(t, s1)
        sprints.start_sprint(s1)
        for t, who in ((t1, marta), (t2, marta), (t3, pedro)):
            for name in ("En desarrollo", "En revisión", "Hecho"):
                backlog.move_task(t, col[name], who)
        backlog.close_sprint(
            s1,
            "Se entregó la guía de estilo y la maqueta.",
            "La auditoría quedó pendiente: mejor estimar con el equipo.",
        )

        # Sprint 2 (activo)
        a = task("Formulario de contacto", marta, 3, parent=story_home)
        b = task("Migrar artículos del blog", pedro, 8, parent=story_blog)
        c = task("Buscador de artículos", pedro, 5, parent=story_blog)
        e = task("Optimizar imágenes", marta, 2)
        f = task("Redactar textos de la página Nosotros", None, 3)
        g = task("Revisión de accesibilidad", luis, 3, start_date=d(-4), due_date=d(-1))  # fechas propias y atrasada
        h = task("Configurar analítica", None, 2, start_date=d(0), due_date=d(2))
        m = task("Publicar anuncio del rediseño", None, 2, start_date=d(-1), due_date=d(3))  # conflicto con g
        s2 = sprints.create_sprint(p, "Sprint 2", "Contenido y formularios", d(-5), d(8))
        for t in (a, b, c, e, f, g, h, m):
            backlog.assign_sprint(t, s2)
        sprints.start_sprint(s2)
        backlog.move_task(e, col["En desarrollo"], marta)
        backlog.move_task(e, col["En revisión"], marta)
        for t, who in ((a, marta), (b, pedro), (c, pedro)):  # En desarrollo queda en 3 / 3
            backlog.move_task(t, col["En desarrollo"], who)
        # dependencias (una con conflicto: el sucesor empieza antes de que termine el predecesor)
        backlog.add_dependency(c, b)
        backlog.add_dependency(a, e)
        backlog.add_dependency(h, g)
        backlog.add_dependency(m, g)

        # Sprint 3 (planificado) y backlog sin sprint
        s3 = sprints.create_sprint(p, "Sprint 3", "Lanzamiento", d(9), d(22))
        i = task("Pruebas de carga", None, 5)
        j = task("Plan de lanzamiento", None, 3)
        task("Redirecciones de URLs antiguas", None, 2)
        task("Capacitar al equipo de contenido", None, 2)
        backlog.assign_sprint(i, s3)
        backlog.add_dependency(j, i)

        # Presupuesto
        for name, amount, cur in (("Marketing", "12000", "USD"), ("Tecnología", "30000", "USD"), ("Diseño", "8000", "EUR")):
            budget.create_department(p, ana, name, amount, cur)

        # ------------------------------------------------ Proyecto 2: pequeño, sin sprint activo
        q = projects.create_project(luis, "Campaña de marketing", "Lanzamiento del segundo trimestre.")
        projects.add_member(q, ana.email, ProjectMember.DEVELOPER)
        backlog.create_task(q, title="Definir público objetivo", estimate_points=2)
        backlog.create_task(q, title="Calendario de redes sociales", estimate_points=3)
        budget.create_department(q, luis, "Marketing", "5000", "USD")

        self.enrich()
        self.stdout.write(self.style.SUCCESS("Datos de demostración creados."))
        self.stdout.write(f"Usuarios (contraseña {PASSWORD}): " + ", ".join(e for e, _ in USERS) + ", paula@demo.com")

    def enrich(self):
        """Empresas, fechas, objetivos, solicitantes y comentarios. Se puede ejecutar varias veces."""
        from apps.backlog.models import Comment, Task
        from apps.projects.models import Company, Project

        User = get_user_model()
        ana, luis, marta, pedro = (User.objects.get(email=e) for e, _ in USERS)
        today = datetime.date.today()
        d = lambda n: today + datetime.timedelta(days=n)  # noqa: E731

        paula, created = User.objects.get_or_create(email="paula@demo.com", defaults={"name": "Paula Project Manager"})
        if created:
            paula.set_password(PASSWORD)
            paula.save()
        rediseno = Project.objects.filter(name="Rediseño del sitio web").first()
        if rediseno and not ProjectMember.objects.filter(project=rediseno, user=paula).exists():
            ProjectMember.objects.create(project=rediseno, user=paula, role=ProjectMember.PROJECT_MANAGER)

        acme, _ = Company.objects.get_or_create(name="Acme S.A.")
        data = {
            "Rediseño del sitio web": (
                acme, d(-21), d(40),
                "Lanzar el nuevo sitio corporativo\nMigrar todo el contenido del blog\nBajar el tiempo de carga a 2 segundos",
            ),
            "Campaña de marketing": (acme, d(-5), d(60), "Conseguir 500 nuevos suscriptores\nPublicar 3 piezas por semana"),
        }
        for name, (company, start, end, objectives) in data.items():
            Project.objects.filter(name=name).update(company=company, start_date=start, end_date=end, objectives=objectives)

        stakeholders = {
            "Como visitante quiero una página de inicio clara": "Dirección comercial",
            "Como lector quiero encontrar los artículos": "Equipo de contenido",
        }
        for title, who in stakeholders.items():
            Task.objects.filter(title=title, kind="story", stakeholder="").update(stakeholder=who)

        # Tercer proyecto, en otra empresa
        if not Project.objects.filter(name="Plataforma de matrículas").exists():
            q = projects.create_project(
                ana,
                "Plataforma de matrículas",
                "Matrícula en línea para padres de familia.",
                company_name="Colegio Santa Ana",
                start_date=d(-10),
                end_date=d(90),
                objectives="Permitir matricularse sin ir al colegio\nReducir el papeleo de secretaría a la mitad",
            )
            projects.add_member(q, luis.email, ProjectMember.SCRUM_MASTER)
            projects.add_member(q, marta.email, ProjectMember.DEVELOPER)
            story = backlog.create_task(
                q, title="Los padres deben poder pagar la matrícula en línea", kind="story", stakeholder="Dirección del colegio"
            )
            backlog.create_task(q, title="Elegir la pasarela de pagos", parent=story, estimate_points=3, assignee=marta)
            backlog.create_task(q, title="Pantalla de resumen de pago", parent=story, estimate_points=2)
            backlog.create_task(
                q, title="Los padres deben ver el estado de la matrícula de cada hijo", kind="story", stakeholder="Secretaría"
            )

        from apps.tickets import services as tickets
        from apps.tickets.models import Ticket

        if not Ticket.objects.exists():
            company = acme
            tickets.create_ticket(ana, company=company, title="Revisar el avance del Sprint 2")
            tickets.create_ticket(ana, company=company, title="Preparar la demo para Dirección", assignee=luis)
            tickets.create_ticket(ana, company=company, title="Confirmar los textos de la página de inicio", assignee=marta)
            tickets.create_ticket(luis, company=company, title="Agendar la retrospectiva", assignee=luis, date=d(-1))
            tickets.create_ticket(luis, company=company, title="Actualizar el tablero de la daily", assignee=pedro)
            done = tickets.create_ticket(luis, company=company, title="Enviar el resumen semanal", assignee=marta)
            tickets.toggle_ticket(done, marta)

        if not Comment.objects.exists():
            story = Task.objects.filter(kind="story", title__startswith="Como visitante").first()
            act = Task.objects.filter(kind="task", title="Formulario de contacto").first()
            if story:
                backlog.add_comment(story, ana, "Dirección pidió que la página de inicio muestre los 3 servicios principales.")
                backlog.add_comment(story, marta, "Entendido. ¿Tenemos los textos finales o uso texto de ejemplo?")
                backlog.add_comment(story, ana, "Usa texto de ejemplo por ahora; los finales llegan el viernes.")
            if act:
                backlog.add_comment(act, pedro, "Necesito saber a qué correo deben llegar los mensajes del formulario.")
                backlog.add_comment(act, luis, "Al correo de contacto de la empresa. Lo confirmo con Ana.")
