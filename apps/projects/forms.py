from django import forms

from .models import Company, ProjectMember

_NON_PO_ROLES = [c for c in ProjectMember.ROLES if c[0] != ProjectMember.PRODUCT_OWNER]
DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


class ProjectForm(forms.Form):
    company = forms.ModelChoiceField(
        label="Empresa", queryset=Company.objects.none(), required=False, empty_label="— Nueva empresa —"
    )
    company_name = forms.CharField(label="Nombre de la empresa nueva", max_length=200, required=False)
    name = forms.CharField(label="Nombre del proyecto", max_length=200)
    description = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    start_date = forms.DateField(label="Fecha de inicio", widget=DATE)
    end_date = forms.DateField(label="Fecha de fin", widget=DATE)
    objectives = forms.CharField(
        label="Objetivos principales (de 1 a 3, uno por línea)",
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Por ejemplo:\nLanzar el nuevo sitio\nReducir el tiempo de carga a 2 segundos"}
        ),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from . import services

        self.fields["company"].queryset = services.companies_for(user)

    def clean(self):
        data = super().clean()
        if not data.get("company") and not (data.get("company_name") or "").strip():
            self.add_error("company_name", "Elige una empresa o escribe el nombre de una nueva.")
        return data


class AddMemberForm(forms.Form):
    email = forms.EmailField(label="Correo")
    role = forms.ChoiceField(label="Rol", choices=_NON_PO_ROLES)


class RoleForm(forms.Form):
    role = forms.ChoiceField(choices=ProjectMember.ROLES)


class TransferForm(forms.Form):
    user_id = forms.IntegerField()
    outgoing_role = forms.ChoiceField(choices=_NON_PO_ROLES)
