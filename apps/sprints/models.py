from django.db import models
from django.db.models import BigIntegerField, Case, F, Q, Value, When


class Sprint(models.Model):
    PLANNED = "planned"
    ACTIVE = "active"
    CLOSED = "closed"
    STATUSES = [(PLANNED, "Planificado"), (ACTIVE, "Activo"), (CLOSED, "Cerrado")]

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="sprints")
    name = models.CharField(max_length=200)
    goal = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=PLANNED)
    review_notes = models.TextField(blank=True)
    retro_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Igual a `project` cuando el sprint está activo y nulo en otro caso: con el índice único
    # garantiza un solo sprint activo por proyecto (los NULL múltiples se admiten en un índice único).
    active_project_id = models.GeneratedField(
        expression=Case(When(status="active", then=F("project_id")), default=Value(None)),
        output_field=BigIntegerField(null=True),
        db_persist=False,
    )

    class Meta:
        ordering = ["start_date", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(end_date__gte=F("start_date")), name="sprint_dates_ordered"),
            models.CheckConstraint(
                condition=Q(status__in=["planned", "active", "closed"]), name="sprint_status_valid"
            ),
            models.UniqueConstraint(fields=["active_project_id"], name="uniq_active_sprint_per_project"),
        ]

    def __str__(self):
        return self.name
