from django import forms
from .models import Venda, Parceiro, Produto, Oferta

class ParceiroForm(forms.ModelForm):
    class Meta:
        model = Parceiro
        fields = ['nome']

        widgets = {
            'nome': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome']

        widgets = {
            'nome': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }


class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ['nome']

        widgets = {
            'nome': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }

class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = [

        ]

        widgets = {
            'contrato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numero do contrato',
                'required': True
            }),
            'contrato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numero do contrato',
                'required': True
            }),
        }