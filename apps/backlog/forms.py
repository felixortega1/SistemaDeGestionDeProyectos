from django import forms
from django.contrib.auth import get_user_model

from .models import Task

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

FULL, ASSIGNEE_ONLY, NO_ASSIGNEE = "full", "assignee_only", "no_assignee"


class TaskForm(forms.Form):
    title = forms.CharField(label="Título", max_length=200)
    kind = forms.ChoiceField(label="Tipo", choices=Task.KINDS, initial=Task.TASK)
    parent = forms.ModelChoiceField(label="Historia padre", queryset=Task.objects.none(), required=False)
    description = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    stakeholder = forms.CharField(label="Solicitado por (solo historias)", max_length=200, required=False)
    estimate_points = forms.IntegerField(label="Puntos", min_value=0, max_value=32767, required=False)
    assignee = forms.ModelChoiceField(label="Responsable", queryset=None, required=False)
    start_date = forms.DateField(label="Inicio propio", required=False, widget=DATE)
    due_date = forms.DateField(label="Fin propio", required=False, widget=DATE)

    def __init__(self, project, *args, mode=FULL, task=None, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["parent"].queryset = Task.objects.filter(project=project, kind=Task.STORY)
        users = User.objects.filter(memberships__project=project)
        if task is not None and task.assignee_id:
            users = User.objects.filter(pk__in=[*users.values_list("pk", flat=True), task.assignee_id])
        self.fields["assignee"].queryset = users
        self.fields["assignee"].label_from_instance = lambda u: u.display_name
        if task is not None:
            del self.fields["kind"]
            if task.kind != Task.STORY:
                del self.fields["stakeholder"]
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


class ActivityForm(forms.Form):
    title = forms.CharField(label="Actividad", max_length=200)
    description = forms.CharField(label="Detalle", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    estimate_points = forms.IntegerField(label="Puntos de esfuerzo", min_value=0, max_value=32767, required=False)
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
        self.fields["depends_on"].queryset = Task.objects.filter(project=task.project, kind=Task.TASK).exclude(pk=task.pk)
