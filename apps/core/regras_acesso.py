class RegrasAcesso:
    def __init__(self, usuario):
        self.usuario = usuario
        self.agente = getattr(usuario, 'agente', None)
        self.perfil = getattr(self.agente, 'perfil', None)

    def model_filter(self, qs):
        if not self.perfil:
            return qs.none()

        perfil = self.perfil.codigo
        escopo = self.perfil.escopo

        if perfil == "ADM":
            return qs

        regras = {
            "SUPERVISOR": self._supervisor_filter,
            "GERENTE": self._gerente_filter,
            "AGENTE": self._agente_filter,
        }

        handler = regras.get(perfil)

        if handler:
            return handler(qs, escopo)

        return qs.none()

    def _supervisor_filter(self, qs, escopo):
        if escopo == 'CARTEIRA':
            return qs.filter(carteira_nome=self.agente.carteira.nome)

        if escopo == 'EQUIPE':
            return qs.filter(equipe_nome=self.agente.equipe.nome)

        return qs.none()


    def _gerente_filter(self, qs, escopo):
        if escopo == 'CARTEIRA':
            return qs.filter(carteira_nome=self.agente.carteira.nome)

        if escopo == 'GLOBAL':
            return qs

        return qs.none()


    def _agente_filter(self, qs, escopo):
        return qs.filter(usuario=self.usuario)