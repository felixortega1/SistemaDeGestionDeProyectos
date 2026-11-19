from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Ticket(models.Model):
    """Pendiente del día de una persona, ligado a una empresa donde participa."""

    OPEN = "open"
    DONE = "done"
    STATUSES = [(OPEN, "Pendiente"), (DONE, "Hecho")]

    company = models.ForeignKey("projects.Company", on_delete=models.PROTECT, related_name="tickets")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=STATUSES, default=OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets")
    created_at = models.DateTimeField(auto_now_add=True)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date", "id"]
        indexes = [models.Index(fields=["assignee", "date"], name="ticket_assignee_date_idx")]
        constraints = [models.CheckConstraint(condition=Q(status__in=["open", "done"]), name="ticket_status_valid")]

    def __str__(self):
        return self.title
