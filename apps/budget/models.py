from django.conf import settings
from django.db import models
from django.db.models import Q


class Department(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=200)
    budget_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["project", "name"], name="uniq_department_name"),
            models.CheckConstraint(condition=Q(budget_amount__gte=0), name="department_budget_nonnegative"),
        ]

    def __str__(self):
        return self.name
