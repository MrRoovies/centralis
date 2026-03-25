from apps.campanhas.models import Campanha, CampanhaCliente

class CampanhaService:
    @staticmethod
    def nao_tabulado(campanha, usuario):
        # Retorna lista de clientes vinculados ao agente para controle e atendimento #
        return (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="CURSO",
            )
            .order_by('prioridade').first()
        )


    @staticmethod
    def agendados(campanha, usuario):
        # Retorna lista de clientes vinculados ao agente para controle e atendimento #
        return (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="AGENDA"
            )
            .order_by('prioridade')
        )



    @staticmethod
    def restantes_mailing(campanha):
        return (CampanhaCliente.objects.filter(
            campanha=campanha,
            situacao__tipo="INICIAL",
        ).count())

    @staticmethod
    def proximo_cliente_para_atendimento(campanha, usuario):
        # 1 Verifica se existe cliente em andamento
        em_curso = (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="CURSO",
            ).first()
        )
        if em_curso:
            return em_curso

        # 2 Verifica se existe cliente em Fila
        proximo = (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(campanha=campanha, situacao__tipo="INICIAL")
            .order_by('prioridade')
            .first()
        )

        return proximo
