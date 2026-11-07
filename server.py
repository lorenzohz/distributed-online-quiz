from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from urllib.parse import urlparse, parse_qs
import json
import argparse
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis de ambiente ao iniciar o script
caminho_env = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=caminho_env)
DB_PASSWORD = os.getenv("DB_PASSWORD")

ENDERECO = "127.0.0.1"

"""
MAPA DE ROTAS DA API REST - QUIZ ONLINE

1. VISUALIZAR RANKING (Tela Inicial)
   - Ação: Retorna as 10 maiores pontuações de jogadores que venceram.
   - Método: GET
   - URL: /ranking
   - Query Params: Nenhum
   - Corpo (JSON): Nenhum
   - Resposta: Lista com as 10 maiores pontuações de jogadores que venceram.

2. INICIAR NOVO JOGO (Tela de Novo Jogo)
   - Ação: Cria uma nova partida e valida se o nickname está disponível.
   - Método: POST
   - URL: /partida
   - Query Params: Nenhum
   - Corpo (JSON): 
        { 
           "nickname": "Lorenzo" 
        }
   - Resposta: ID para a nova partida criada.

3. OBTER PERGUNTA (Tela de Pergunta)
   - Ação: Sorteia e retorna a próxima pergunta baseada na rodada atual.
   - Método: GET
   - URL: /pergunta?partida_id=<ID_DA_PARTIDA>
   - Query Params: partida_id (Ex: /pergunta?partida_id=5)
   - Corpo (JSON): Nenhum
   - Resposta: Pergunta para ser respondida.

4. ENVIAR RESPOSTA (Ação do Jogador)
   - Ação: Avalia a resposta, calcula bônus por tempo e atualiza estado.
   - Método: POST
   - URL: /responder
   - Query Params: Nenhum
   - Corpo (JSON): 
        {
           "partida_id": 5,
           "questao_id": 42,
           "alternativa_escolhida": "b",
           "tempo_segundos": 15
        }
    - Resposta: 

5. SOLICITAR AJUDA (Ação do Jogador)
   - Ação: Processa o uso de "meio_a_meio", "pulo" ou "passe_livre".
   - Método: POST
   - URL: /ajuda
   - Query Params: Nenhum
   - Corpo (JSON):
        {
           "partida_id": 5,
           "questao_id": 42,
           "tipo_ajuda": "meio_a_meio" 
        }
    - Resposta: 
"""

class ServidorREST(BaseHTTPRequestHandler):

    def obter_conexao(self):
        """Cria e retorna uma nova conexão com o banco de dados."""
        return psycopg2.connect(
            dbname="quiz_online",
            user="postgres",
            password=DB_PASSWORD,
            host="127.0.0.1",
            port="5432"
        )

    def do_GET(self):
        url = urlparse(self.path)
        operacao = url.path
        parametros = parse_qs(url.query) 

        if operacao == "/ranking":
            conexao = None
            cursor = None
            try:
                conexao = self.obter_conexao()
                cursor = conexao.cursor()
                
                # Busca os 10 melhores que venceram o jogo
                query = """
                    SELECT nickname, pontuacao 
                    FROM partidas 
                    WHERE status = 'venceu' 
                    ORDER BY pontuacao DESC 
                    LIMIT 10
                """
                cursor.execute(query)
                resultados = cursor.fetchall()
                
                # Converte a lista de tuplas em uma lista de dicionários
                ranking = [{"nickname": linha[0], "pontuacao": linha[1]} for linha in resultados]
                
                self.enviar_resposta(200, {"ranking": ranking})

            except Exception as e:
                print(f"Erro no banco de dados: {e}")
                self.enviar_resposta(500, {"erro": "Erro interno no servidor"})

            finally:
                # Fecha as portas com o banco
                if cursor:
                    cursor.close()
                if conexao:
                    conexao.close()
            
        elif operacao == "/pergunta":
            # Extrai o partida_id da URL (ex: /pergunta?partida_id=5)
            partida_id_lista = parametros.get("partida_id")
            
            if not partida_id_lista:
                self.enviar_resposta(400, {"erro": "Parâmetro 'partida_id' não fornecido."})
                return
                
            partida_id = partida_id_lista[0]
            
            conexao = None
            cursor = None
            try:
                conexao = self.obter_conexao()
                cursor = conexao.cursor()
                
                # 1. Obter o estado atual da partida
                cursor.execute("""
                    SELECT pergunta_atual, ajuda_meio_a_meio_usada, 
                           ajuda_pulo_usada, ajuda_passe_livre_usada, status 
                    FROM partidas WHERE id = %s
                """, (partida_id,))
                
                estado_partida = cursor.fetchone()
                
                if not estado_partida:
                    self.enviar_resposta(404, {"erro": "Partida não encontrada."})
                    return
                    
                pergunta_atual, meio_usada, pulo_usado, passe_usado, status = estado_partida
                
                # Impede que o cliente puxe perguntas de um jogo que já acabou
                if status != 'em_andamento':
                    self.enviar_resposta(400, {"erro": f"Jogo encerrado. Status atual: {status}"})
                    return
                
                # 2. Determinar o nível com base na rodada
                if pergunta_atual <= 3:
                    nivel_alvo = 'facil'
                elif pergunta_atual <= 6:
                    nivel_alvo = 'medio'
                elif pergunta_atual <= 9:
                    nivel_alvo = 'dificil'
                elif pergunta_atual == 10:
                    nivel_alvo = 'final'
                else:
                    self.enviar_resposta(400, {"erro": "Todas as 10 perguntas já foram respondidas."})
                    return

                # 3. Sortear uma pergunta que o jogador ainda não respondeu
                # Obs.: A subquery (NOT IN) garante que a pergunta não está no histórico da partida
                # Obs.: ORDER BY RANDOM() faz o sorteio
                query_sorteio = """
                    SELECT id, enunciado, alt_a, alt_b, alt_c, alt_d 
                    FROM questoes 
                    WHERE nivel = %s 
                      AND id NOT IN (SELECT questao_id FROM perguntas_partida WHERE partida_id = %s)
                    ORDER BY RANDOM() 
                    LIMIT 1
                """
                cursor.execute(query_sorteio, (nivel_alvo, partida_id))
                questao = cursor.fetchone()
                
                if not questao:
                    self.enviar_resposta(500, {"erro": f"Não há questões no banco de questões ainda não respondidas suficientes do nível '{nivel_alvo}'."})
                    return
                    
                questao_id, enunciado, alt_a, alt_b, alt_c, alt_d = questao

                # 4. Registrar a pergunta no histórico da partida
                cursor.execute("""
                    INSERT INTO perguntas_partida (partida_id, questao_id, ordem) 
                    VALUES (%s, %s, %s)
                """, (partida_id, questao_id, pergunta_atual))
                
                # Salva as alterações no banco (o registro da pergunta)
                conexao.commit()

                # 5. Montar o JSON de resposta
                resposta = {
                    "questao_id": questao_id,
                    "ordem": pergunta_atual,
                    "nivel": nivel_alvo,
                    "enunciado": enunciado,
                    "alternativas": {
                        "a": alt_a,
                        "b": alt_b,
                        "c": alt_c,
                        "d": alt_d
                    },
                    "ajudas_disponiveis": {
                        "meio_a_meio": not meio_usada,
                        "pulo": not pulo_usado,
                        "passe_livre": not passe_usado
                    }
                }
                
                self.enviar_resposta(200, resposta)

            except Exception as e:
                # Se der erro no meio do caminho, desfaz o INSERT da pergunta_partida
                if conexao:
                    conexao.rollback()
                print(f"Erro no banco de dados (/pergunta): {e}")
                self.enviar_resposta(500, {"erro": "Erro interno no servidor"})

            finally:
                if cursor: cursor.close()
                if conexao: conexao.close()
            
        else:
            self.enviar_resposta(404, {"erro": "Rota GET nao encontrada"})

    def do_POST(self):
        url = urlparse(self.path)
        operacao = url.path
        
        tamanho_conteudo = int(self.headers.get('Content-Length', 0))
        if tamanho_conteudo > 0:
            corpo_bytes = self.rfile.read(tamanho_conteudo)
            dados_recebidos = json.loads(corpo_bytes.decode('utf-8'))
        else:
            dados_recebidos = {}

        if operacao == "/partida":
            nickname = dados_recebidos.get("nickname")
            
            if not nickname:
                self.enviar_resposta(400, {"erro": "Nickname não fornecido"})
                return

            conexao = None
            cursor = None
            try:
                conexao = self.obter_conexao()
                cursor = conexao.cursor()
                
                # Insere o nickname e já retorna o ID gerado automaticamente
                query = "INSERT INTO partidas (nickname) VALUES (%s) RETURNING id"
                cursor.execute(query, (nickname,))
                
                nova_partida_id = cursor.fetchone()[0]
                
                # Efetiva a gravação no banco
                conexao.commit() 
                
                self.enviar_resposta(201, {
                    "sucesso": True, 
                    "partida_id": nova_partida_id,
                    "mensagem": f"Bem-vindo, {nickname}!"
                })

            except psycopg2.IntegrityError:
                # Cai aqui automaticamente se violar a restrição UNIQUE do banco (nickname já existe)
                if conexao:
                    conexao.rollback()
                self.enviar_resposta(400, {"erro": "Este nickname já está em uso. Escolha outro."})

            except Exception as e:
                if conexao:
                    conexao.rollback()
                print(f"Erro no banco de dados: {e}")
                self.enviar_resposta(500, {"erro": "Erro interno no servidor"})

            finally:
                if cursor:
                    cursor.close()
                if conexao:
                    conexao.close()

        elif operacao == "/responder":
            partida_id = dados_recebidos.get("partida_id")
            questao_id = dados_recebidos.get("questao_id")
            alternativa_escolhida = dados_recebidos.get("alternativa_escolhida")
            tempo_segundos = dados_recebidos.get("tempo_segundos")

            conexao = None
            cursor = None
            try:
                conexao = self.obter_conexao()
                cursor = conexao.cursor()
                
                # Busca a resposta correta para a questão alvo
                query = """ SELECT nivel, alt_correta 
                            FROM questoes 
                            WHERE questao_id = %s"""
                cursor.execute(query, (questao_id,))
                
                nivel, alternativa_correta = cursor.fetchone()

                pontuacao = __conta_pontuacao_pergunta(nivel, tempo_segundos)

                if alternativa_escolhida == alternativa_correta:
                    self.enviar_resposta(201, {
                        "acertou":True,
                        "pontuacao":pontuacao,
                    })

            except Exception as e:
                if conexao:
                    conexao.rollback()
                print(f"Erro no banco de dados: {e}")
                self.enviar_resposta(500, {"erro": "Erro interno no servidor"})

            finally:
                if cursor:
                    cursor.close()
                if conexao:
                    conexao.close()

        elif operacao == "/ajuda":
            self.enviar_resposta(200, {"mensagem": "Lógica de ajudas pendente"})

        else:
            self.enviar_resposta(404, {"erro": "Rota POST nao encontrada"})


    def enviar_resposta(self, codigo, resposta):
        conteudo = json.dumps(resposta).encode('utf-8')

        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", f"{len(conteudo)}")
        self.end_headers()

        self.wfile.write(conteudo)

def __conta_pontuacao_pergunta(nivel, tempo):
    """Contabiliza quantos pontos a questão resultou"""
    if nivel == "facil":
        pontos = 50
        fator = 1
    elif nivel == "medio":
        pontos = 100
        fator = 1.5
    elif nivel == "dificil":
        pontos = 300
        fator = 2
    elif nivel == "final":
        pontos = 1000
        fator = 10

    return round(pontos + max(0, (60 - tempo)) * fator, 3)


if __name__ == "__main__":
    # Configuração do parser de argumentos da CLI
    parser = argparse.ArgumentParser(description="Nó Servidor REST do Quiz Online")
    parser.add_argument("-p", "--porta", type=int, default=8000, help="Porta de execução do servidor (padrão: 8000)")
    
    args = parser.parse_args()
    porta_escolhida = args.porta

    servidor = HTTPServer((ENDERECO, porta_escolhida), ServidorREST)
    print(f"Servidor REST (Nó Servidor) iniciado em {ENDERECO}:{porta_escolhida}, aguardando requisições...")
    
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor de forma segura...")
        servidor.server_close()