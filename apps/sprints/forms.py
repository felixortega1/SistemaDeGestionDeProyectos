from django import forms

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class SprintForm(forms.Form):
    name = forms.CharField(label="Nombre", max_length=200)
    goal = forms.CharField(label="Objetivo", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    start_date = forms.DateField(label="Inicio", required=False, widget=DATE)
    end_date = forms.DateField(label="Fin", required=False, widget=DATE)


class CloseSprintForm(forms.Form):
    review_notes = forms.CharField(label="Notas de review", widget=forms.Textarea(attrs={"rows": 2}), required=False)
    retro_notes = forms.CharField(label="Notas de retrospectiva", widget=forms.Textarea(attrs={"rows": 2}), required=False)
