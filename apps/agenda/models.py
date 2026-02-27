from django.db import models
from django.conf import settings
from ..usuarios.models import Carteira, Perfil, Equipe

# ========================
# MODEL AGENDA
# ========================
class Agenda(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    perfil = models.ForeignKey(
        Perfil,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    carteira = models.ForeignKey(
        Carteira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    telefone = models.CharField('Telefone de Contato', max_length=11, blank=True, null=True)
    situacao = models.ForeignKey(
        "Situacao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    data_entrada = models.DateTimeField('Data Entrada', auto_now_add=True)
    data_hora_retorno = models.DateTimeField('Retorno Chamada', blank=True, null=True)
    data_finalizado = models.DateTimeField('Data Finalizado', null=True, blank=True)
    agenda_ativa = models.BooleanField(default=True)  # Pode receber acionamentos
    modo = models.CharField('Modo Atendimento', max_length=50, blank=False, null=False)  # Ativo/Receptivo
    canal = models.CharField('Canal Atendimento', max_length=50, blank=False, null=False)  # WhatsApp/Email/Mailing

    # Snapshot para histórico (nome da equipe/perfil/carteira no momento)
    equipe_nome = models.CharField(max_length=100, blank=True, null=True)
    perfil_nome = models.CharField(max_length=50, blank=True, null=True)
    carteira_nome = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-data_entrada']

    def __str__(self):
        situ = self.situacao.nome if self.situacao else 'Sem Situação'
        return f"{self.usuario.get_full_name()} - {situ} - {self.data_entrada.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Atualiza snapshot
        if self.equipe:
            self.equipe_nome = self.equipe.nome
        if self.perfil:
            self.perfil_nome = self.perfil.codigo
        if self.carteira:
            self.carteira_nome = self.carteira.nome

        # Atualiza agenda_ativa automaticamente
        if self.situacao and self.situacao.tipo != "AGENDA":
            self.agenda_ativa = False

        # Validação antes de salvar
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Impede múltiplas agendas ativas para o mesmo cliente na mesma carteira
        enquanto a situação estiver "Em Atendimento" ou "Agendado".
        """
        from django.core.exceptions import ValidationError

        if not self.agenda_ativa or not self.carteira:
            return

        # Situações que bloqueiam outro usuário da mesma carteira
        bloqueio_tipos = ["AGENDA"]  # "Em Atendimento"/"Agendado" é do tipo "AGENDA"

        qs = Agenda.objects.filter(
            usuario=self.usuario,
            carteira=self.carteira,
            agenda_ativa=True,
            situacao__tipo__in=bloqueio_tipos
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError(
                f"Este cliente já possui uma agenda ativa na mesma carteira."
            )

# ========================
# MODEL ACIONAMENTO
# ========================
class Acionamento(models.Model):
    agenda = models.ForeignKey("Agenda", on_delete=models.CASCADE)
    data_acionamento = models.DateTimeField("Data Acionamento", auto_now_add=True)
    data_finalizado = models.DateTimeField("Data Finalizado", null=True, blank=True)
    situacao = models.ForeignKey("Situacao", on_delete=models.CASCADE)
    comentario = models.TextField("Comentario", max_length=1024, null=True, blank=True)

    class Meta:
        ordering = ['-data_acionamento']



    def __str__(self):
        return f"{self.agenda} - {self.situacao.nome} ({self.data_acionamento.strftime('%d/%m/%Y %H:%M')})"

# ========================
# MODEL SITUACAO
# ========================
class Situacao(models.Model):
    TIPO_CHOICES = [
        ('INICIAL', 'Inicial'),
        ('AGENDA', 'Agendamento'),
        ('INSUCESSO', 'Insucesso'),
        ('SUCESSO', 'Sucesso')
    ]
    nome = models.CharField('Situacao', max_length=50, blank=False, null=False)
    tipo = models.CharField('Tipo', choices=TIPO_CHOICES, blank=False, null=False)
    carteira = models.ForeignKey(Carteira, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('nome', 'carteira')
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.tipo})"