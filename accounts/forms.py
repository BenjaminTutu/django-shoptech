from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Phone')
    address = forms.CharField(required=False, label='Address')

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'address' ,'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label
            if field == self.fields['password2']:
                field.widget.attrs['placeholder'] = 'Confirm Password'


class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():

            # add bootstrap styling
            field.widget.attrs['class'] = 'form-control'

            # add placeholders
            field.widget.attrs['placeholder'] = field.label