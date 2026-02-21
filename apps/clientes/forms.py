from django import forms
from .models import Cliente, Email, Telefone


class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa',
            'nome',
            'documento',
            'data_nascimento',
            'estado_civil',
            'nome_mae',
        ]

        widgets = {
            'tipo_pessoa': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome completo',
                'autocomplete': 'name'
            }),
            'documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CPF ou CNPJ',
                'maxlength': '14',
                'autocomplete': 'off'
            }),
            'data_nascimento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'estado_civil': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nome_mae': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da Mãe',
                'maxlength': '255',
                'autocomplete': 'off'
            }),

        }

class EmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = [
            'email',
            'tipo',
        ]
        widgets = {
            'email': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

class TelefoneForm(forms.ModelForm):
    class Meta:
        model = Telefone
        fields = [
            'telefone',
            'tipo',
            'whats_app'
        ]
        SIM_NAO = (
            (True, 'Sim'),
            (False, 'Não')
        )
        widgets = {
            'telefone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'whats_app': forms.Select(
                choices = SIM_NAO,
                attrs = {'class': 'form-control'}
            ),
        }