from django import forms
from .models import Cliente, Email, Telefone, Endereco


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
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        # Se já existe no banco → estamos editando
        if self.instance and self.instance.pk:
            self.fields['documento'].disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)

        # 🔒 Blindagem absoluta
        if self.instance.pk:
            original = type(self.instance).objects.get(pk=self.instance.pk)

            instance.documento = original.documento

        if commit:
            instance.save()

        return instance

    def clean_documento(self):
        from django.core.exceptions import ValidationError
        documento = self.cleaned_data['documento']

        if Cliente.objects.filter(
            empresa=self.empresa,
            documento=documento
        ).exists():
            raise ValidationError("Já existe um cliente com esse documento.")

        return documento


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

class EnderecoForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = [
            'logradouro',
            'numero',
            'bairro',
            'cidade',
            'uf',
            'cep',
            'tipo'
        ]

        widgets = {
            'logradouro': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'uf': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }