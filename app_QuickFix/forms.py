from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'cidade', 'estado', 'profile_image']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
