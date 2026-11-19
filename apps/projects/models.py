from django.conf import settings
from django.db import models


class Company(models.Model):
    """Empresa u organización. Un usuario la ve cuando participa en alguno de sus proyectos."""

    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class Project(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="projects", null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    objectives = models.TextField(blank=True, help_text="Entre 1 y 3 objetivos principales, uno por línea.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(end_date__gte=models.F("start_date")), name="project_dates_ordered"),
        ]

    @property
    def objective_list(self):
        return [line.strip() for line in self.objectives.splitlines() if line.strip()]

    def __str__(self):
        return self.name


class ProjectMember(models.Model):
    PRODUCT_OWNER = "product_owner"
    PROJECT_MANAGER = "project_manager"
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"
    ROLES = [
        (PRODUCT_OWNER, "Product Owner"),
        (PROJECT_MANAGER, "Project Manager"),
        (SCRUM_MASTER, "Scrum Master"),
        (DEVELOPER, "Equipo de desarrollo"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="uniq_project_member"),
            models.CheckConstraint(
                condition=models.Q(role__in=["product_owner", "project_manager", "scrum_master", "developer"]),
                name="projectmember_role_valid",
            ),
        ]

    def __str__(self):
        return f"{self.user} ({self.role})"
