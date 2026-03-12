from django.utils import timezone
from django.db.models import Q
from django.db import models
from django.conf import settings
from ..usuarios.models import Carteira, Perfil, Equipe
from ..clientes.models import Cliente

# ========================
# MODEL AGENDA
# ========================
class Agenda(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='agendas'
    )
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
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'carteira'],
                condition=Q(agenda_ativa=True),
                name='unique_active_agenda_per_carteira'
            )
        ]

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

        if self.situacao_id:
            # Se situacao já está em cache (via select_related), usa direto
            # Se não está, busca só o campo tipo — sem carregar o objeto inteiro
            if 'situacao' in self.__dict__:
                tipo = self.situacao.tipo
            else:
                tipo = Situacao.objects.filter(
                    pk=self.situacao_id
                ).values_list('tipo', flat=True).first()

            if tipo and tipo not in ["AGENDA", "CURSO"]:
                self.agenda_ativa = False

        # Validação antes de salvar
        super().save(*args, **kwargs)


# ========================
# MODEL ACIONAMENTO
# ========================
class Acionamento(models.Model):
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE)
    data_acionamento = models.DateTimeField("Data Acionamento", auto_now_add=True)
    data_finalizado = models.DateTimeField("Data Finalizado", null=True, blank=True)
    situacao = models.ForeignKey("Situacao", on_delete=models.CASCADE)
    comentario = models.TextField("Comentario", max_length=1024, null=True, blank=True)

    class Meta:
        ordering = ['-data_acionamento']
        constraints = [
            models.UniqueConstraint(
                fields=["agenda"],
                condition=models.Q(data_finalizado__isnull=True),
                name='unique_open_acionamento_per_agenda'
            )
        ]

    @property
    def tempo_tela(self):
        """
        Retorna um timedelta bruto (bom para cálculos e relatórios).
        """
        if not self.data_finalizado:
            return timezone.now() - self.data_acionamento
        else:
            return self.data_finalizado - self.data_acionamento

    @property
    def tempo_tela_formatado(self):
        """
        Retorna string formatada: Xd Xh Xm Xs
        """
        if not self.tempo_tela:
            return "-"

        total_segundos = int(self.tempo_tela.total_seconds())

        dias, resto = divmod(total_segundos, 86400)
        horas, resto = divmod(resto, 3600)
        minutos, segundos = divmod(resto, 60)

        partes = []
        if dias:
            partes.append(f"{dias}d")
        if horas:
            partes.append(f"{horas}h")
        if minutos:
            partes.append(f"{minutos}m")
        if segundos or not partes:
            partes.append(f"{segundos}s")

        return " ".join(partes)

    def __str__(self):
        return f"{self.agenda} - {self.situacao.nome} ({self.data_acionamento.strftime('%d/%m/%Y %H:%M')})"

# ========================
# MODEL SITUACAO
# ========================
class Situacao(models.Model):
    TIPO_CHOICES = [
        ('INICIAL', 'Inicial'),
        ('CURSO', 'Em Atendimento'),
        ('AGENDA', 'Agendamento'),
        ('INSUCESSO', 'Insucesso'),
        ('SUCESSO', 'Sucesso')
    ]
    nome = models.CharField('Situacao', max_length=50, blank=False, null=False)
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES, blank=False, null=False)
    carteira = models.ForeignKey(Carteira, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('nome', 'carteira')
        ordering = ['tipo']

    def __str__(self):
        return f"{self.nome} ({self.tipo})"