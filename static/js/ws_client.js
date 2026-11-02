// ws_client.js — cliente do ws_server.py (Python puro).
//
// getToken é uma função (pode ser async) que devolve um token válido.
// É chamada a cada (re)conexão, então token expirado nunca trava o cliente.
//
// Uso:
//   const ws = new AppSocket({
//       url: 'ws://localhost:8765/ws',
//       getToken: async () => (await fetch('/api/ws-token/')).json().then(r => r.token),
//   });
//   ws.on('conectado', (dados) => console.log('online', dados));
//   ws.on('chamada_atendida', (dados) => { ... });
//   ws.send('meu_tipo', { qualquer: 'coisa' });
//
// Protocolo: {"tipo": "...", "dados": {...}} nos dois sentidos.

class AppSocket {
    constructor({ url, getToken }) {
        this.url = url;
        this.getToken = getToken;
        this.handlers = {};
        this.fila = [];            // enviado enquanto desconectado -> vai ao reconectar
        this.tentativa = 0;
        this.fechadoPorMim = false;
        this.conectar();
    }

    on(tipo, fn) {
        (this.handlers[tipo] ||= []).push(fn);
        return this;
    }

    off(tipo, fn) {
        this.handlers[tipo] = (this.handlers[tipo] || []).filter(f => f !== fn);
    }

    send(tipo, dados = {}) {
        const msg = JSON.stringify({ tipo, dados });
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(msg);
        } else {
            this.fila.push(msg);
        }
    }

    close() {
        this.fechadoPorMim = true;
        clearInterval(this.heartbeat);
        if (this.ws) this.ws.close();
    }

    agendarReconexao() {
        if (this.fechadoPorMim) return;
        const espera = Math.min(1000 * 2 ** this.tentativa, 30000);
        this.tentativa++;
        setTimeout(() => this.conectar(), espera);
    }

    async conectar() {
        let token;
        try {
            token = await this.getToken();
        } catch (err) {
            console.error('Falha ao obter token do WebSocket', err);
            return this.agendarReconexao();
        }

        this.ws = new WebSocket(`${this.url}?token=${encodeURIComponent(token)}`);

        this.ws.onopen = () => {
            this.tentativa = 0;
            this.fila.splice(0).forEach(m => this.ws.send(m));
            clearInterval(this.heartbeat);
            this.heartbeat = setInterval(() => this.send('ping'), 25000);
        };

        this.ws.onmessage = (e) => {
            let msg;
            try { msg = JSON.parse(e.data); } catch { return; }
            (this.handlers[msg.tipo] || []).forEach(fn => {
                try { fn(msg.dados, msg); } catch (err) { console.error('Erro no handler', msg.tipo, err); }
            });
        };

        this.ws.onclose = () => {
            clearInterval(this.heartbeat);
            this.agendarReconexao();
        };
    }
}

  const ws = new AppSocket({
    url: "ws://localhost:8765/ws",
    getToken: async () => (await fetch('/api/ws-token/')).json().then(r => r.token),
  });
  ws.on('conectado', (d) => console.log('WS online', d));