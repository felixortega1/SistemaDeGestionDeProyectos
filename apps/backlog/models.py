from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Epic(models.Model):
    """Agrupa historias de un proyecto bajo un mismo tema. Las actividades heredan la épica de su historia."""

    DEFAULT_COLOR = "#EAB308"

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="epics")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default=DEFAULT_COLOR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title", "id"]

    def __str__(self):
        return self.title


class Story(models.Model):
    """Historia de usuario: algo que alguien necesita. Se reparte en tareas y tiene criterios de aceptación."""

    HIGH, MEDIUM, LOW = "high", "medium", "low"
    PRIORITIES = [(HIGH, "Alta"), (MEDIUM, "Media"), (LOW, "Baja")]

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="stories")
    epic = models.ForeignKey(Epic, on_delete=models.PROTECT, null=True, blank=True, related_name="stories")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    stakeholder = models.CharField(max_length=200, blank=True, help_text="Quién pidió esta historia.")
    priority = models.CharField(max_length=10, choices=PRIORITIES, default=MEDIUM)
    estimate_points = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(priority__in=["high", "medium", "low"]), name="story_priority_valid"),
        ]

    def __str__(self):
        return self.title


class AcceptanceCriterion(models.Model):
    """Punto de la lista de verificación de una historia."""

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="criteria")
    text = models.CharField(max_length=500)
    is_done = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]


class Task(models.Model):
    """Tarea ejecutable: lo que alguien hace. Puede pertenecer a una historia o estar suelta."""

    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="tasks")
    story = models.ForeignKey(Story, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    sprint = models.ForeignKey("sprints.Sprint", on_delete=models.PROTECT, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
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
            models.CheckConstraint(
                condition=(Q(sprint__isnull=True, column__isnull=True) | Q(sprint__isnull=False, column__isnull=False)),
                name="task_sprint_column_together",
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
    """Comentario de un miembro del proyecto sobre una historia o una tarea (exactamente una de las dos)."""

    story = models.ForeignKey(Story, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(story__isnull=False, task__isnull=True) | Q(story__isnull=True, task__isnull=False),
                name="comment_story_xor_task",
            ),
        ]

    @property
    def target(self):
        return self.story if self.story_id else self.task

    @property
    def project(self):
        return self.target.project
