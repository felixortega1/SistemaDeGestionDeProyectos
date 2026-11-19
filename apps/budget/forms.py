from django import forms


class DepartmentForm(forms.Form):
    name = forms.CharField(label="Departamento", max_length=200)
    budget_amount = forms.DecimalField(label="Monto", max_digits=14, decimal_places=2, min_value=0)
    currency = forms.CharField(label="Moneda (3 letras)", min_length=3, max_length=3)

    def clean_currency(self):
        value = self.cleaned_data["currency"]
        if not (value.isalpha() and value.isascii() and value.isupper()):
            raise forms.ValidationError("Usa un código de tres letras mayúsculas, por ejemplo USD.")
        return value
