from django import forms


class ColumnForm(forms.Form):
    name = forms.CharField(label="Nombre", max_length=200)
    wip_limit = forms.IntegerField(label="Límite WIP (vacío = sin límite)", min_value=0, max_value=32767, required=False)
    policy_text = forms.CharField(label="Política", widget=forms.Textarea(attrs={"rows": 2}), required=False)


class MoveForm(forms.Form):
    column_id = forms.IntegerField()
