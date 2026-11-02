"""
Discagem via GoTo Connect API (calls/v2/calls)
Fluxo conforme a documentação oficial: developer.goto.com

Usa o fluxo de Personal Access Token (PAT) em vez do authorization_code
via navegador — indicado quando você já é o dono/admin da conta e não
precisa de consentimento de terceiros a cada execução.

Passos:
  0. (feito uma vez, manualmente, fora do código):
       - Gerar um PAT em https://myaccount.goto.com > Developer Tools > Create token
       - Habilitar o Grant Type "Personal Access Token" no seu OAuth Client
         em https://developer.logmeininc.com/clients
  1. Trocar o PAT por um access_token
  2. Buscar o accountKey do usuário autenticado (Admin API /me)
  3. Buscar a lineId do usuário (Users API)
  4. Discar via POST /calls/v2/calls

Scopes necessários (tanto no OAuth Client quanto no PAT):
  - calls.v2.initiate
  - users.v1.lines.read

Requer: pip install requests --break-system-packages
"""

import base64
import requests

# ---------------------------------------------------------------------------
# Configuração — preencha com os dados do seu OAuth Client e do seu PAT
# ---------------------------------------------------------------------------
CLIENT_ID = "4711c7d9-a46c-4e4c-a295-d3d52d896e7d"
CLIENT_SECRET = "6AC6twz64rQj9j9D6TrYUmeu"
PERSONAL_ACCESS_TOKEN = "1855980482981396907_ggkldeXaNUiZQGfubzamrljlbCBdwzd4"  # gerado em myaccount.goto.com > Developer Tools

AUTH_BASE_URL = "https://authentication.logmeininc.com/oauth"
ADMIN_API = "https://api.getgo.com/admin/rest/v1"
USERS_API = "https://api.goto.com/users/v1"
CALLS_API = "https://api.goto.com/calls/v2"
 
class DiscadorService():
    def exchange_pat_for_token(self) -> dict:
        """
        Passo 1: troca o Personal Access Token por um access_token de API.
        Autenticação via HTTP Basic (client_id:client_secret em base64).
        """
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        basic_auth = base64.b64encode(credentials.encode()).decode()
    
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "personal_access_token",
            "pat": PERSONAL_ACCESS_TOKEN,
        }
    
        response = requests.post(f"{AUTH_BASE_URL}/token", headers=headers, data=data)
        if not response.status_code == 200:
            return {'success': False, 'message': f'Exgange Token Error: {response.text}'}

        token_data = response.json()
        
        return {'success': True, 'access_token': token_data.get('access_token')}
    
    
    def get_account_key(self, access_token: str) -> str:
        """
        Passo 2: busca as contas do usuário autenticado via Admin API /me.
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.get(f"{ADMIN_API}/me", headers=headers)
        response.raise_for_status()
        me = response.json()
    
        accounts = me.get("accounts", [])
        if not accounts:
            return {'success': False, 'message': "Nenhuma conta encontrada para este usuário."}
    
        account_key = accounts[0]["key"]

        return {'success': True, 'account_key': account_key}
    
    
    def find_user_key_by_email(self, access_token: str, account_key: str, email: str) -> str:
        """
        Resolve o e-mail vindo do CRM para o userKey do GoTo Connect.
    
        Usa a Admin API (Get Users), que retorna o cadastro completo dos
        usuários da conta, incluindo email — o mesmo campo usado ao criar/
        atualizar usuários nessa API. Fazemos o filtro no próprio código
        para não depender de sintaxe de filtro server-side não documentada.
    
        OBS: se sua conta tiver muitos usuários, verifique no Postman/OpenAPI
        de developer.goto.com/admin se há paginação (nextPage/cursor) a tratar.
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        params = {"consistency": "eventual"}
        response = requests.get(
            f"{ADMIN_API}/accounts/{account_key}/users", headers=headers, params=params
        )
        if not response.status_code == 200:
            return {'success': False, 'message': f"Buscar usuário: {response.text}"}
        
        data = response.json()
    
        # A resposta pode vir como lista direta ou dentro de "results"/"items",
        # dependendo da versão — cobrimos os formatos mais comuns.
        users = data if isinstance(data, list) else data.get("results", data.get("items", []))
        email_lower = email.strip().lower()
        
        for user in users:
            if str(user.get("email", "")).strip().lower() == email_lower:
                user_key = str(user.get("key") or user.get("userKey"))
                
                return {'success': True, 'user_key': user_key }
    
        return {'success': False, 'message': f"Nenhum usuário com e-mail '{email}' encontrado na conta {account_key}."}
    
    
    def get_line_id_by_user_key(self, access_token: str, account_key: str, user_key: str) -> str:
        """
        Busca a lineId associada a um userKey específico (não o primeiro
        usuário da lista, e sim o usuário resolvido a partir do e-mail do CRM).
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        params = {"accountKey": account_key}
        response = requests.get(f"{USERS_API}/users", headers=headers, params=params)
        if not response.status_code == 200:
            return {'success': False, 'message': f"LineId: {response.text}"} 
        
        users = response.json().get("items", [])
    
        for user in users:
            if str(user.get("userKey")) == str(user_key):
                lines = user.get("lines", [])
                if not lines:
                    return {'success': False, 'message': f"O usuário {user_key} não possui nenhuma linha cadastrada."}
                    
                line = lines[0]
                return {'success': True, 'line_id': line["id"]}

        return {'success': False, 'message': f"userKey {user_key} não encontrado na lista de usuários da conta."} 
        
     
    def make_call(self, access_token: str, line_id: str, dial_string: str) -> dict:
        """
        Passo 5: efetua a discagem via POST /calls/v2/calls.
        O telefone/softphone associado a line_id toca; ao ser atendido,
        a chamada é conectada ao número em dial_string.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "dialString": dial_string,
            "from": {"lineId": line_id},
        }
        response = requests.post(f"{CALLS_API}/calls", headers=headers, json=payload)
        print(response)
        if not response.status_code == 200:
            return {'success': False, 'message': f"Make call: {response}"}


    def inicia_discador(self, user, telefones):
        for fone in telefones:
            # numero = fone.telefone
            numero = 5511987757011
            
            token_data = self.exchange_pat_for_token()
            if not token_data.get('success'):
                return token_data
                
            access_token = token_data["access_token"]
            
            # 2. Conta
            get_account_key = self.get_account_key(access_token)
            if not get_account_key.get('success'):
                return get_account_key

            account_key = get_account_key['account_key']

            # 3. Resolve o e-mail do CRM para o userKey do GoTo, depois para a lineId
            user_key = self.find_user_key_by_email(access_token, account_key, user.agente.email)
            if not user_key.get('success'):
                return user_key

            user_key = user_key.get('user_key')

            line_id = self.get_line_id_by_user_key(access_token, account_key, user_key)
            if not line_id.get('success'):
                return line_id

            line_id = line_id.get('line_id')

            # 4. Discagem
            result = self.make_call(access_token, line_id, numero)
            if not result.get('success'):
                return result

            return {'success': True}