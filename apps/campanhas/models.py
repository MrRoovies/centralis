from django.db import models
from django.conf import settings
from django.db.models.functions import Lower


# Create your models here.
class Campanha(models.Model):
    empresa = models.ForeignKey("core.Empresa", on_delete=models.CASCADE)
    CHOICE_TIPOS = [
        ("MANUAL", "Manual"),
        ("DISCADOR", "Discador"),
        ("EXLEAD", "Lead Externo")
    ]
    CHOICE_METODO = [("ORDENADO", "Ordenado"), ("ALEATORIO", "Aleatorio")]

    nome = models.CharField("Nome Campanha", max_length=80, null=False, blank=False)
    modo_atendimento = models.CharField("Modo Atendimento", choices=CHOICE_TIPOS, max_length=10, null=False, blank=False)
    distribuicao_ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Define quais situacoes, parceiros e produtos vao aparecer na boletagem
    carteira = models.ForeignKey("usuarios.Carteira", on_delete=models.CASCADE)
    metodo_distribuicao = models.CharField("Indice Sorteio", choices=CHOICE_METODO, max_length=10, null=False, blank=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower('nome'),
                'carteira',
                name="unique_nome_carteira"
            )
        ]

    def __str__(self):
         return f"{self.carteira.nome} - {self.nome}"

class CampanhaAgente(models.Model):
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE)
    agente = models.ForeignKey("usuarios.Agente", on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("campanha", "agente")

    def __str__(self):
        return f"{self.campanha} - {self.agente}"


class CampanhaCliente(models.Model):
    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.PROTECT)
    agente_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    situacao = models.ForeignKey("agenda.Situacao", on_delete=models.PROTECT)
    agenda = models.ForeignKey("agenda.Agenda", on_delete=models.SET_NULL, null=True, blank=True)
    prioridade = models.PositiveIntegerField(db_index=True)
    tentativas = models.IntegerField(default=0)
    ultima_tentativa = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("cliente", "campanha")
        indexes = [
            models.Index(fields=["campanha", "situacao", "prioridade"])
        ]


    def __str__(self):
        return f"{self.campanha} - {self.cliente} - {self.situacao}"

