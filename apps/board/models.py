from django.db import models


class BoardColumn(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="columns")
    name = models.CharField(max_length=200)
    position = models.PositiveIntegerField()
    wip_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    policy_text = models.TextField(blank=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.name


class ColumnTransition(models.Model):
    from_column = models.ForeignKey(BoardColumn, on_delete=models.CASCADE, related_name="transitions_out")
    to_column = models.ForeignKey(BoardColumn, on_delete=models.CASCADE, related_name="transitions_in")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["from_column", "to_column"], name="uniq_column_transition"),
        ]
