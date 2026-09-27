from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

ENDERECO = "127.0.0.1"
PORTA= 8000


class ServidorREST(BaseHTTPRequestHandler):

    def do_GET(self):
        url = urlparse(self.path)
        operacao = url.path
        parametros = parse_qs(url.query)
        a = float(parametros["a"][0])
        b = float(parametros["b"][0])

        if operacao == "/somar":
            resultado = a + b
        elif operacao == "/multiplicar":
            resultado = a * b
        elif operacao == "/subtrair":
            resultado = a - b
        elif operacao == "/dividir":
            resultado = a / b

        self.enviar_resposta(200, {"resultado" : resultado})


    def enviar_resposta(self, codigo, resposta):

        conteudo = json.dumps(resposta).encode()

        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", f"{len(conteudo)}")

        self.end_headers()

        self.wfile.write(conteudo)


#codigo principal
servidor = HTTPServer((ENDERECO, PORTA), ServidorREST)

print("Servidor REST iniciado, aguardando requisições...")

servidor.serve_forever()
