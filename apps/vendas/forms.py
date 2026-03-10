from django import forms
from .models import Parceiro, Produto, Venda, Oferta, Esteira, HistVenda


class VendaForm(forms.ModelForm):
    parceiro = forms.ModelChoiceField(
        queryset=Parceiro.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Parceiro'
    )
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Produto'
    )


    class Meta:
        model = Venda
        fields = [
            'contrato',
            'oferta',
            'prazo',
            'parcela',
            'valor',
        ]

        widgets = {
            'contrato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número do contrato',
                'required': True
            }),
            'oferta': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'prazo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prazo em meses',
                'min': 1,
                'required': True
            }),
            'parcela': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'step': '0.01',
                'min': 0,
                'required': True
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0,00',
                'step': '0.01',
                'min': 0,
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields['parceiro'].queryset = Parceiro.objects.filter(empresa=empresa, ativo=True)
            self.fields['produto'].queryset = Produto.objects.none()  # populado via JS
            self.fields['oferta'].queryset = Oferta.objects.none()    # populado via JS

    def clean(self):
        cleaned_data = super().clean()
        oferta = cleaned_data.get('oferta')
        prazo = cleaned_data.get('prazo')

        if oferta and prazo:
            if prazo < oferta.prazo_min or prazo > oferta.prazo_max:
                raise forms.ValidationError(
                    f"Prazo deve estar entre {oferta.prazo_min} e {oferta.prazo_max} meses para esta oferta."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Snapshot do produto e parceiro no momento da venda
        if instance.oferta:
            instance.produto_nome = instance.oferta.produto.nome
            instance.parceiro_nome = instance.oferta.parceiro.nome
            instance.comissao = instance.oferta.comissao

        if commit:
            instance.save()

        return instance


class HistVendaForm(forms.ModelForm):
    class Meta:
        model = HistVenda
        fields = ['esteira', 'comentario']

        widgets = {
            'esteira': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Comentário sobre a movimentação...',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        carteira = kwargs.pop('carteira', None)
        super().__init__(*args, **kwargs)

        # Filtra esteiras pela empresa e carteira do agente
        qs = Esteira.objects.filter(ativo=True)
        if empresa:
            qs = qs.filter(empresa=empresa)
        if carteira:
            qs = qs.filter(carteira=carteira)

        self.fields['esteira'].queryset = qs.order_by('ordem')