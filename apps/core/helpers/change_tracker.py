
class ChangeTracker:
    @staticmethod
    def verifica_alteracoes(model, dados):
        alteracoes = []
        campos_model = {f.name for f in model._meta.fields}
        for campo, novo_valor in dados.items():
            if campo not in campos_model:
                continue
            valor_antigo = getattr(model, campo, None)

            print(str(valor_antigo), str(novo_valor))
            # normaliza pra string pra evitar problema com Decimal, etc
            if str(valor_antigo) != str(novo_valor):
                alteracoes.append(
                    f"{campo} alterado: {valor_antigo} → {novo_valor}"
                )

        return alteracoes