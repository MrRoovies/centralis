from datetime import date
from django.db import models
from django.conf import settings
from ..core.models import Empresa


# ==========================================
# MODELS DE NEGÓCIO - AGENTES E ORGANIZAÇÃO
# ==========================================

# ========================
# Model Agente
# ========================
class Agente(models.Model):
    """
    Representa um agente/usuário do sistema.

    Relacionamentos:
    - usuario: FK para o User do Django (autenticação)
    - equipe: FK para Equipe (organização de agentes)
    - perfil: FK para Perfil (papel comercial / hierarquia)
      * Para multi-perfil, usar um model intermediário AgentePerfil
    - carteira: FK para Carteira (segmento de negócio / funil / produtos)
    - email, nascimento, cpf: dados pessoais
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    equipe = models.ForeignKey(
        "Equipe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    perfil = models.ForeignKey(
        "Perfil",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    carteira = models.ForeignKey("Carteira", on_delete=models.SET_NULL, null=True)
    email = models.EmailField('E-mail', max_length=200, null=True, blank=True)
    nascimento = models.DateField('Nascimento')
    cpf = models.CharField('Cpf', max_length=11, blank=False, null=False)

    class Meta:
        verbose_name = "Agente"
        verbose_name_plural = "Agentes"
        ordering = ["carteira"]

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.perfil}"

    def idade(self):
        """Calcula a idade do agente."""
        hoje = date.today()
        if not self.nascimento:
            return None
        idade = hoje.year - self.nascimento.year

        # Ajusta se ainda não fez aniversário este ano
        if (hoje.month, hoje.day) < (self.nascimento.month, self.nascimento.day):
            idade -= 1

        return idade


# ========================
# Model Carteira
# ========================
class Carteira(models.Model):
    """
    Representa a carteira de clientes / segmento de negócio.

    Relacionamentos:
    - empresa: FK para Empresa (cada carteira pertence a uma empresa)

    Funções:
    - Define funis e situações disponíveis para os agentes.
    """
    nome = models.CharField('Nome Carteira', max_length=50)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.empresa.nome})"


# ========================
# Model Equipe
# ========================
class Equipe(models.Model):
    """
    Representa uma equipe de agentes dentro da empresa.

    Relacionamentos:
    - responsavel: FK para User (pode ser null)

    Funções:
    - Agrupa agentes para fins de visibilidade e metas.
    """
    nome = models.CharField('Nome', max_length=100)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    data_create = models.DateTimeField('Data Criacao', auto_now_add=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


# ========================
# Model Perfil
# ========================
from django.contrib.auth.models import Group

class Perfil(models.Model):
    """
    Representa o papel/comportamento do agente.

    Cada Perfil está ligado a um Group do Django para controle de permissões.
    """
    PERFIL_CHOICES = [
        ('ADM', 'Administrador'),
        ('DIRETOR', 'Diretor'),
        ('GERENTE', 'Gerente'),
        ('SUPERVISOR', 'Supervisor'),
        ('AGENTE', 'Agente'),
        ('VISITANTE', 'Visitante')
    ]
    codigo = models.CharField('Perfil', max_length=50, choices=PERFIL_CHOICES)
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    data_create = models.DateTimeField('Data Criacao', auto_now=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.get_codigo_display()


# ==========================================
# OPCIONAL: Model intermediário Agente ↔ Perfil
# ==========================================
class AgentePerfil(models.Model):
    """
    Model intermediário para suportar:
    - Multi-perfil por agente
    - Swap de perfil ativo
    - Histórico de atribuições

    Relacionamentos:
    - agente: FK para Agente
    - perfil: FK para Perfil
    """
    agente = models.ForeignKey(Agente, on_delete=models.CASCADE)
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=False)  # Perfil atualmente em uso
    data_inicio = models.DateField(auto_now_add=True)
    data_fim = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("agente", "perfil")  # impede duplicação
        verbose_name = "Agente - Perfil"
        verbose_name_plural = "Agentes - Perfis"

    def __str__(self):
        status = "Ativo" if self.ativo else "Inativo"
        return f"{self.agente.usuario.get_full_name()} - {self.perfil} ({status})"