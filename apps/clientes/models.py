from datetime import date

from django.db import models

# Create your models here.
class Cliente(models.Model):

    TIPO_PESSOA = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]

    ESTADO_CIVIL_CHOICES = [
        ('SOLTEIRO', 'Solteiro(a)'),
        ('CASADO', 'Casado(a)'),
        ('DIVORCIADO', 'Divorciado(a)'),
        ('VIUVO', 'Viúvo(a)'),
        ('UNIAO_ESTAVEL', 'União Estável'),
    ]
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE, related_name="clientes")
    nome = models.CharField('Nome', max_length=255)
    tipo_pessoa = models.CharField('Tipo Pessoa', max_length=2, choices=TIPO_PESSOA)

    documento = models.CharField(
        'Documento',
        max_length=14,
        help_text="CPF (11) ou CNPJ (14) somente números"
    )

    rg = models.CharField('RG', max_length=20, blank=True, null=True)
    data_nascimento = models.DateField('Nascimento', blank=True, null=True)
    nome_mae = models.CharField('Nome da Mãe', max_length=255, blank=True, null=True)
    nome_pai = models.CharField('Nome do Pai', max_length=255, blank=True, null=True)

    estado_civil = models.CharField(
        'Estado Civil',
        max_length=20,
        choices=ESTADO_CIVIL_CHOICES,
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'documento'],
                name='unique_cpf_por_empresa'
            )
        ]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']

    def idade(self):
        hoje = date.today()
        if not self.data_nascimento:
            return None

        idade = hoje.year - self.data_nascimento.year

        # Se ainda não fez aniversário esse ano
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1

        return idade

    def clean(self):
        import re
        from django.core.exceptions import ValidationError

        self.documento = re.sub(r'\D', '', self.documento)

        if self.tipo_pessoa == 'PF':
            if len(self.documento) != 11:
                raise ValidationError("CPF deve ter 11 dígitos.")
            if not self.data_nascimento:
                raise ValidationError("Pessoa Física deve ter data de nascimento.")

        if self.tipo_pessoa == 'PJ':
            if len(self.documento) != 14:
                raise ValidationError("CNPJ deve ter 14 dígitos.")
            if self.rg:
                raise ValidationError("Pessoa Jurídica não deve possuir RG.")

    def __str__(self):
        return f"{self.nome} - {self.documento}"

class Email(models.Model):
    EMAIL_CHOICES = [
        ('PESSOAL','Pessoal'),
        ('CORPORATIVO','Corporativo')
    ]

    cliente = models.ForeignKey(
        "Cliente",
        on_delete=models.CASCADE,
        related_name="emails"
    )

    email = models.EmailField(max_length=255, db_index=True, blank=True)
    tipo = models.CharField(max_length=11, choices=EMAIL_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'email', 'tipo'],
                name='unique_email_cliente'
            )
        ]

    @classmethod
    def get_existente(cls, cliente_id, email, tipo):
        return cls.objects.filter(
            cliente_id=cliente_id,
            email=email,
            tipo=tipo
        ).first()

    def __str__(self):
        return self.email


class Telefone(models.Model):
    TELEFONE_CHOICES = [
        ('FIXO', 'Fixo'),
        ('CELULAR', 'Celular'),
        ('CORPORATIVO', 'Corporativo'),
    ]

    cliente = models.ForeignKey(
        "Cliente",
        on_delete=models.CASCADE,
        related_name="telefones"
    )

    telefone = models.CharField(max_length=11, db_index=True, blank=True)
    tipo = models.CharField(max_length=15, choices=TELEFONE_CHOICES, blank=True)
    whats_app = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'telefone'],
                name='unique_telefone_cliente'
            )
        ]

    def clean(self):
        import re
        from django.core.exceptions import ValidationError

        self.telefone = re.sub(r'\D', '', self.telefone)

        if len(self.telefone) not in [10, 11]:
            raise ValidationError("Telefone deve ter 10 ou 11 dígitos.")

    def __str__(self):
        return self.telefone


class Endereco(models.Model):
    ENDERECO_CHOICES = [
        ('RESIDENCIAL', 'Residencial'),
        ('COMERCIAL', 'Comercial')
    ]

    cliente = models.ForeignKey(
        "Cliente",
        on_delete=models.CASCADE,
        related_name="enderecos"
    )
    logradouro = models.CharField('Logra.', max_length=100)
    numero = models.CharField('Numero', max_length=10)
    bairro = models.CharField('Bairro', max_length=255)
    cidade = models.CharField('Cidade', max_length=200)
    uf = models.CharField('UF', max_length=2)
    cep = models.CharField('Cep', max_length=10)
    tipo = models.CharField('Tipo Endereco', max_length=15, choices=ENDERECO_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'logradouro', 'numero', 'cep', 'tipo'],
                name='unique_endereco_cliente_tipo'
            )
        ]

    def clean(self):
        import re
        from django.core.exceptions import ValidationError

        self.numero = re.sub(r'\D', '', self.numero)
        self.cep = re.sub(r'\D', '', self.cep)

        if len(self.cep) != 8:
            raise ValidationError("Cep Incorreto.")