from django.db import models
from django.conf import settings


class Parceiro(models.Model):
    empresa = models.ForeignKey(
        "core.Empresa",
        on_delete=models.PROTECT,
        related_name="parceiros"
    )

    nome = models.CharField("Parceiro", max_length=150)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome}"


class Produto(models.Model):
    empresa = models.ForeignKey(
        "core.Empresa",
        on_delete=models.CASCADE,
        related_name="produtos"
    )

    nome = models.CharField("Produto", max_length=150)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Oferta(models.Model):
    empresa = models.ForeignKey(
        "core.Empresa",
        on_delete=models.CASCADE,
        related_name="ofertas"
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="ofertas"
    )

    parceiro = models.ForeignKey(
        Parceiro,
        on_delete=models.PROTECT,
        related_name="ofertas"
    )

    prazo_min = models.PositiveSmallIntegerField("Min. Prazo")
    prazo_max = models.PositiveSmallIntegerField("Max. Prazo")

    comissao = models.DecimalField(
        "Comissão %",
        max_digits=5,
        decimal_places=2
    )

    ativo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "produto", "parceiro"],
                name="unique_oferta_empresa_produto_parceiro"
            )
        ]

    def __str__(self):
        return f"{self.produto} - {self.parceiro}"


class Esteira(models.Model):

    class TipoEsteira(models.TextChoices):
        INICIAL = "INICIAL", "Inicial"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        SUCESSO = "SUCESSO", "Sucesso"
        INSUCESSO = "INSUCESSO", "Insucesso"

    empresa = models.ForeignKey(
        "core.Empresa",
        on_delete=models.CASCADE,
        related_name="esteiras"
    )

    carteira = models.ForeignKey(
        "usuarios.Carteira",
        on_delete=models.CASCADE,
        related_name="esteiras"
    )

    nome = models.CharField("Esteira", max_length=50)

    tipo = models.CharField(
        "Tipo",
        max_length=20,
        choices=TipoEsteira.choices
    )

    ordem = models.PositiveSmallIntegerField("Ordem do funil")

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Venda(models.Model):

    empresa = models.ForeignKey(
        "core.Empresa",
        on_delete=models.CASCADE,
        related_name="vendas"
    )

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="vendas"
    )
    contrato = models.PositiveSmallIntegerField("Nr. Contrato")

    oferta = models.ForeignKey(
        Oferta,
        on_delete=models.PROTECT,
        related_name="vendas"
    )

    # snapshot da oferta
    produto_nome = models.CharField("Produto nome", max_length=150)
    parceiro_nome = models.CharField("Parceito nome", max_length=150)

    prazo = models.PositiveSmallIntegerField("Prazo")

    parcela = models.DecimalField(
        "Valor Parcela",
        max_digits=10,
        decimal_places=2
    )

    valor = models.DecimalField(
        "Valor Contrato",
        max_digits=12,
        decimal_places=2
    )

    comissao = models.DecimalField(
        "Comissão aplicada %",
        max_digits=5,
        decimal_places=2
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vendas"
    )

    agenda = models.ForeignKey(
        "agenda.Agenda",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vendas"
    )

    carteira = models.CharField("Carteira", max_length=50)

    equipe = models.CharField("Equipe", max_length=100)

    esteira = models.ForeignKey(
        Esteira,
        on_delete=models.PROTECT,
        related_name="vendas"
    )

    data_venda = models.DateTimeField(
        "Data Boletagem",
        auto_now_add=True
    )

    def __str__(self):
        return f"Venda {self.id} - {self.cliente}"


class HistVenda(models.Model):

    venda = models.ForeignKey(
        Venda,
        on_delete=models.PROTECT,
        related_name="historico"
    )

    esteira = models.ForeignKey(
        Esteira,
        on_delete=models.PROTECT
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )

    comentario = models.TextField(
        "Comentário",
        max_length=1024,
        blank=True
    )

    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.venda} -> {self.esteira}"