class RegrasAcesso:
    def __init__(self, usuario):
        self.usuario = usuario

    def model_filter(self, qs):
        perfil = self.usuario.agente.perfil.codigo
        escopo = self.usuario.agente.perfil.escopo

        if perfil == "ADM":
            return qs

        if perfil == "SUPERVISOR":
            if escopo == 'CARTEIRA':
                return qs.filter(carteira_nome=self.usuario.agente.carteira.nome)
            if escopo == 'EQUIPE':
                return qs.filter(equipe_nome=self.usuario.agente.equipe.nome)

        if perfil == "GERENTE":
            if escopo == 'CARTEIRA':
                return qs.filter(carteira_nome=self.usuario.agente.carteira.nome)
            if escopo == 'GLOBAL':
                return qs

        if perfil == "AGENTE":
            return qs.filter(usuario=self.usuario)
