from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from .models import Epic, Story, Task

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

FULL, ASSIGNEE_ONLY, NO_ASSIGNEE = "full", "assignee_only", "no_assignee"
POINTS_HELP = "Escala sugerida: 1-2 (S), 3-5 (M), 8 (L)."
HEX_COLOR = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "El color debe tener el formato #RRGGBB.")


class TaskForm(forms.Form):
    title = forms.CharField(label="Título", max_length=200)
    story = forms.ModelChoiceField(label="Historia", queryset=Story.objects.none(), required=False)
    description = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    estimate_points = forms.IntegerField(
        label="Puntos", min_value=0, max_value=32767, required=False, help_text=POINTS_HELP
    )
    assignee = forms.ModelChoiceField(label="Responsable", queryset=None, required=False)
    start_date = forms.DateField(label="Inicio propio", required=False, widget=DATE)
    due_date = forms.DateField(label="Fin propio", required=False, widget=DATE)

    def __init__(self, project, *args, mode=FULL, task=None, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["story"].queryset = Story.objects.filter(project=project)
        self.fields["story"].label_from_instance = lambda s: s.title
        users = User.objects.filter(memberships__project=project)
        if task is not None and task.assignee_id:
            users = User.objects.filter(pk__in=[*users.values_list("pk", flat=True), task.assignee_id])
        self.fields["assignee"].queryset = users
        self.fields["assignee"].label_from_instance = lambda u: u.display_name
        if mode == NO_ASSIGNEE:
            del self.fields["assignee"]
        elif mode == ASSIGNEE_ONLY:
            for name in list(self.fields):
                if name != "assignee":
                    del self.fields[name]


class StoryForm(forms.Form):
    title = forms.CharField(
        label="¿Qué necesita el usuario o el cliente?",
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "Por ejemplo: el usuario debe poder pagar con tarjeta"}),
    )
    stakeholder = forms.CharField(
        label="¿Quién lo pidió?",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Por ejemplo: Dirección comercial"}),
    )
    description = forms.CharField(label="Detalle", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    epic = forms.ModelChoiceField(label="Épica", queryset=Epic.objects.none(), required=False)
    priority = forms.ChoiceField(label="Prioridad", choices=Story.PRIORITIES, initial=Story.MEDIUM, required=False)
    estimate_points = forms.IntegerField(
        label="Puntos", min_value=0, max_value=32767, required=False, help_text=POINTS_HELP
    )

    def clean_priority(self):
        return self.cleaned_data.get("priority") or Story.MEDIUM

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["epic"].queryset = Epic.objects.filter(project=project)


class EpicForm(forms.Form):
    title = forms.CharField(label="Título de la épica", max_length=200)
    description = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    color = forms.CharField(
        label="Color",
        max_length=7,
        initial=Epic.DEFAULT_COLOR,
        validators=[HEX_COLOR],
        widget=forms.TextInput(attrs={"type": "color"}),
    )


class CriterionForm(forms.Form):
    text = forms.CharField(
        label="Nuevo criterio",
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "Por ejemplo: el pago se confirma por correo"}),
    )


class BacklogFilterForm(forms.Form):
    """Filtros por GET. `priority` es la de la historia; `epic` acepta un id o `none` (sin épica)."""

    priority = forms.ChoiceField(choices=[("", "Todas"), *Story.PRIORITIES], required=False)
    epic = forms.CharField(required=False)


class StoryTaskForm(forms.Form):
    title = forms.CharField(label="Tarea", max_length=200)
    description = forms.CharField(label="Detalle", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    estimate_points = forms.IntegerField(
        label="Puntos de esfuerzo", min_value=0, max_value=32767, required=False, help_text=POINTS_HELP
    )
    assignee = forms.ModelChoiceField(label="Responsable", queryset=None, required=False)

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["assignee"].queryset = User.objects.filter(memberships__project=project)
        self.fields["assignee"].label_from_instance = lambda u: u.display_name


class CommentForm(forms.Form):
    body = forms.CharField(label="Escribe un comentario", widget=forms.Textarea(attrs={"rows": 3}), max_length=4000)


class MilestoneForm(forms.Form):
    name = forms.CharField(label="Nombre", max_length=200)
    date = forms.DateField(label="Fecha", widget=DATE)


class AssignSprintForm(forms.Form):
    sprint_id = forms.IntegerField()
    next = forms.CharField(required=False)


class DependencyForm(forms.Form):
    depends_on = forms.ModelChoiceField(label="Depende de", queryset=Task.objects.none())

    def __init__(self, task, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["depends_on"].queryset = Task.objects.filter(project=task.project).exclude(pk=task.pk)
