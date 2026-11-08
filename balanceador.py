import argparse
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import json
import logging
import threading


SERVIDORES = (
    ("A", "127.0.0.1", 8001),
    ("B", "127.0.0.1", 8002),
    ("C", "127.0.0.1", 8003),
)
CABECALHOS_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class BalanceadorRR:
    def __init__(self, servidores):
        self.servidores = servidores
        self.proximo = 0
        self.lock = threading.Lock()

    def selecionar(self):
        with self.lock:
            servidor = self.servidores[self.proximo]
            self.proximo = (self.proximo + 1) % len(self.servidores)
            return servidor


class ManipuladorBalanceador(BaseHTTPRequestHandler):
    balanceador = None
    timeout = 30

    def do_GET(self):
        self.encaminhar()

    def do_HEAD(self):
        self.encaminhar()

    def do_POST(self):
        self.encaminhar()

    def do_PUT(self):
        self.encaminhar()

    def do_PATCH(self):
        self.encaminhar()

    def do_DELETE(self):
        self.encaminhar()

    def do_OPTIONS(self):
        self.encaminhar()

    def encaminhar(self):
        servidor = self.balanceador.selecionar()
        nome, host, porta = servidor
        cliente_ip, cliente_porta = self.client_address[:2]
        horario = datetime.now().astimezone().isoformat(timespec="seconds")
        logging.info(
            "%s:%s;%s %s;%s;%s",
            cliente_ip,
            cliente_porta,
            self.command,
            self.path,
            horario,
            nome,
        )

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if tamanho < 0:
                raise ValueError("Content-Length inválido")
            corpo = self.rfile.read(tamanho) if tamanho else None
        except ValueError:
            self.enviar_erro(HTTPStatus.BAD_REQUEST, "Content-Length inválido")
            return

        cabecalhos_conexao = {
            token.strip().lower()
            for valor in self.headers.get_all("Connection", [])
            for token in valor.split(",")
        }
        cabecalhos = {
            nome: valor
            for nome, valor in self.headers.items()
            if nome.lower() not in CABECALHOS_HOP_BY_HOP | cabecalhos_conexao | {"host"}
        }

        conexao = http.client.HTTPConnection(host, porta, timeout=self.timeout)
        try:
            conexao.request(self.command, self.path, body=corpo, headers=cabecalhos)
            resposta = conexao.getresponse()
            conteudo = resposta.read()
            cabecalhos_resposta_conexao = {
                token.strip().lower()
                for valor in resposta.headers.get_all("Connection", [])
                for token in valor.split(",")
            }
        except (OSError, http.client.HTTPException) as erro:
            logging.exception("Falha ao encaminhar para o servidor %s", nome)
            self.enviar_erro(
                HTTPStatus.BAD_GATEWAY,
                f"Servidor {nome} indisponível: {erro}",
            )
            return
        finally:
            conexao.close()

        self.send_response(resposta.status, resposta.reason)
        for nome_cabecalho, valor in resposta.getheaders():
            if nome_cabecalho.lower() not in (
                CABECALHOS_HOP_BY_HOP | cabecalhos_resposta_conexao | {"server", "date"}
            ):
                self.send_header(nome_cabecalho, valor)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(conteudo)

    def enviar_erro(self, status, mensagem):
        corpo = json.dumps({"erro": mensagem}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corpo)

    def log_message(self, formato, *args):
        logging.debug("%s - %s", self.address_string(), formato % args)


def main():
    parser = argparse.ArgumentParser(description="Balanceador HTTP Round-Robin do Quiz")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta")
    parser.add_argument("--porta", type=int, default=8000, help="Porta de escuta")
    parser.add_argument(
        "--log",
        default="balanceador.log",
        help="Arquivo para registrar as requisições",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="Tempo máximo de espera pelos servidores, em segundos",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(args.log, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    manipulador = type(
        "ManipuladorBalanceadorConfigurado",
        (ManipuladorBalanceador,),
        {"balanceador": BalanceadorRR(SERVIDORES), "timeout": args.timeout},
    )
    servidor = ThreadingHTTPServer((args.host, args.porta), manipulador)
    servidor.daemon_threads = True
    print(f"Balanceador RR iniciado em {args.host}:{args.porta}")
    print("Servidores: " + ", ".join(f"{nome}={host}:{porta}" for nome, host, porta in SERVIDORES))

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando balanceador...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
