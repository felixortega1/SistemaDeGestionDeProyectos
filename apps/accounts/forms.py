from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterForm(forms.Form):
    name = forms.CharField(label="Nombre", max_length=200)
    email = forms.EmailField(label="Correo")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repite la contraseña", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            else:
                try:
                    validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        return data

    def save(self):
        d = self.cleaned_data
        return User.objects.create_user(d["email"], d["password1"], name=d["name"])


class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        email, password = data.get("email"), data.get("password")
        if email and password:
            self.user = authenticate(self.request, username=email.lower(), password=password)
            if self.user is None:
                raise forms.ValidationError("Correo o contraseña incorrectos.")
        return data
