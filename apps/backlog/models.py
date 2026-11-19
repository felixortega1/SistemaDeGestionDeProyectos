from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Task(models.Model):
    STORY = "story"
    TASK = "task"
    KINDS = [(STORY, "Historia"), (TASK, "Tarea")]

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="tasks")
    sprint = models.ForeignKey("sprints.Sprint", on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="children")
    kind = models.CharField(max_length=10, choices=KINDS, default=TASK)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stakeholder = models.CharField(max_length=200, blank=True, help_text="Quién pidió esta historia.")
    column = models.ForeignKey("board.BoardColumn", on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    estimate_points = models.PositiveSmallIntegerField(null=True, blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="assigned_tasks"
    )
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sprint", "column"], name="task_sprint_column_idx"),
            models.Index(fields=["project", "sprint", "column"], name="task_proj_sprint_col_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(kind__in=["story", "task"]), name="task_kind_valid"),
            models.CheckConstraint(
                condition=(Q(sprint__isnull=True, column__isnull=True) | Q(sprint__isnull=False, column__isnull=False)),
                name="task_sprint_column_together",
            ),
            models.CheckConstraint(
                condition=Q(kind="task")
                | Q(
                    sprint__isnull=True,
                    column__isnull=True,
                    start_date__isnull=True,
                    due_date__isnull=True,
                    parent__isnull=True,
                ),
                name="task_story_has_no_planning",
            ),
        ]

    def __str__(self):
        return self.title


class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="dependencies")
    depends_on = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="dependents")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "depends_on"], name="uniq_task_dependency"),
            models.CheckConstraint(condition=~Q(task=F("depends_on")), name="task_dependency_not_self"),
        ]


class Milestone(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=200)
    date = models.DateField()

    class Meta:
        ordering = ["date", "id"]

    def __str__(self):
        return self.name


class SprintTask(models.Model):
    sprint = models.ForeignKey("sprints.Sprint", on_delete=models.PROTECT, related_name="history")
    task = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="sprint_history")
    column_name = models.CharField(max_length=200)
    is_done = models.BooleanField()
    estimate_points = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sprint", "task"], name="uniq_sprint_task")]


class Comment(models.Model):
    """Comentario de un miembro del proyecto sobre una historia o una actividad."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
