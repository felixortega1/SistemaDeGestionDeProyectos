from django import forms
from django.contrib.auth import get_user_model

from apps.projects.services import companies_for

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class TicketForm(forms.Form):
    title = forms.CharField(label="¿Qué hay que hacer hoy?", max_length=200)
    company = forms.ModelChoiceField(label="Empresa", queryset=None)
    description = forms.CharField(label="Detalle", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    date = forms.DateField(label="Día", widget=DATE, required=False)
    assignee = forms.ModelChoiceField(label="Asignar a", queryset=None, required=False, empty_label="Yo")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = companies_for(user)
        self.fields["assignee"].queryset = get_user_model().objects.filter(
            memberships__project__company__in=companies_for(user)
        ).distinct()
        self.fields["assignee"].label_from_instance = lambda u: u.display_name
