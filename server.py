from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import math
from random import sample
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
    - Resposta: {"acertou": true/false, "pontuacao": <pontos atribuídos>}.

5. SOLICITAR AJUDA (Ação do Jogador)
   - Ação: Processa o uso de "meio_a_meio", "pulo" ou "passe_livre".
   - Método: POST
   - URL: /ajuda
   - Query Params: Nenhum
   - Corpo (JSON):
        {
           "partida_id": 5,
           "questao_id": 42,
           "tipo_ajuda": 1 
        }
    - Resposta: Ajuda aplicada e disponibilidades atualizadas. O "meio_a_meio"
      retorna as alternativas restantes; "pulo" retorna a questão substituta;
      "passe_livre" retorna "avancou": true e concede apenas os pontos-base
      da questão, sem bônus por tempo.
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
            try:
                partida_id = int(partida_id)
            except ValueError:
                self.enviar_resposta(400, {"erro": "Parâmetro 'partida_id' inválido."})
                return
            if partida_id <= 0:
                self.enviar_resposta(400, {"erro": "Parâmetro 'partida_id' inválido."})
                return
            
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
                    FOR UPDATE
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

                # Reuse the active question if this request is retried.
                cursor.execute("""
                    SELECT q.id, q.enunciado, q.alt_a, q.alt_b, q.alt_c, q.alt_d
                    FROM perguntas_partida pp
                    JOIN questoes q ON q.id = pp.questao_id
                    WHERE pp.partida_id = %s AND pp.ordem = %s
                      AND pp.usou_pulo = FALSE
                      AND pp.usou_passe_livre = FALSE
                    ORDER BY pp.id DESC
                    LIMIT 1
                """, (partida_id, pergunta_atual))
                questao = cursor.fetchone()
                pergunta_ja_registrada = questao is not None

                # 3. Sorteia uma questão que ainda não aparece no histórico da partida.
                query_sorteio = """
                    SELECT id, enunciado, alt_a, alt_b, alt_c, alt_d 
                    FROM questoes 
                    WHERE nivel = %s 
                      AND NOT EXISTS (
                          SELECT 1 FROM perguntas_partida
                          WHERE partida_id = %s AND questao_id = questoes.id
                      )
                    ORDER BY RANDOM() 
                    LIMIT 1
                """
                if not questao:
                    cursor.execute(query_sorteio, (nivel_alvo, partida_id))
                    questao = cursor.fetchone()

                if not questao:
                    self.enviar_resposta(500, {"erro": f"Não há questões no banco de questões ainda não respondidas suficientes do nível '{nivel_alvo}'."})
                    return
                    
                questao_id, enunciado, alt_a, alt_b, alt_c, alt_d = questao

                # 4. Registrar a pergunta no histórico da partida
                if not pergunta_ja_registrada:
                    cursor.execute("""
                        INSERT INTO perguntas_partida (partida_id, questao_id, ordem)
                        VALUES (%s, %s, %s)
                    """, (partida_id, questao_id, pergunta_atual))
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
                        "passe_livre": not passe_usado and pergunta_atual < 10
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
            try:
                dados_recebidos = json.loads(corpo_bytes.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.enviar_resposta(400, {"erro": "Corpo da requisição deve conter JSON válido."})
                return
        else:
            dados_recebidos = {}
        if not isinstance(dados_recebidos, dict):
            self.enviar_resposta(400, {"erro": "Corpo da requisição deve ser um objeto JSON."})
            return

        if operacao == "/partida":
            nickname = dados_recebidos.get("nickname")
            if not isinstance(nickname, str) or not nickname.strip() or len(nickname.strip()) > 50:
                self.enviar_resposta(400, {"erro": "Nickname inválido. Use de 1 a 50 caracteres."})
                return
            nickname = nickname.strip()

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

            try:
                partida_id = int(partida_id)
                questao_id = int(questao_id)
                tempo_segundos = float(tempo_segundos)
            except (TypeError, ValueError):
                self.enviar_resposta(400, {"erro": "Dados da resposta inválidos."})
                return

            if partida_id <= 0 or questao_id <= 0 or not math.isfinite(tempo_segundos) or tempo_segundos < 0:
                self.enviar_resposta(400, {"erro": "Dados da resposta inválidos."})
                return
            if not isinstance(alternativa_escolhida, str) or alternativa_escolhida.lower() not in ("a", "b", "c", "d"):
                self.enviar_resposta(400, {"erro": "Alternativa escolhida inválida."})
                return
            alternativa_escolhida = alternativa_escolhida.lower()

            conexao = None
            cursor = None
            try:
                conexao = self.obter_conexao()
                cursor = conexao.cursor()
                cursor.execute("""
                    SELECT pergunta_atual, status
                    FROM partidas
                    WHERE id = %s
                    FOR UPDATE
                """, (partida_id,))
                partida = cursor.fetchone()
                if not partida:
                    self.enviar_resposta(404, {"erro": "Partida não encontrada."})
                    return

                ordem_atual, status = partida
                if status != "em_andamento":
                    self.enviar_resposta(409, {"erro": f"Jogo encerrado. Status atual: {status}"})
                    return

                cursor.execute("""
                    SELECT pp.id, pp.questao_id, q.nivel, q.alt_correta
                    FROM perguntas_partida pp
                    JOIN questoes q ON q.id = pp.questao_id
                    WHERE pp.partida_id = %s AND pp.ordem = %s
                    ORDER BY pp.id DESC
                    LIMIT 1
                    FOR UPDATE OF pp
                """, (partida_id, ordem_atual))
                pergunta = cursor.fetchone()
                if not pergunta or pergunta[1] != questao_id:
                    self.enviar_resposta(409, {"erro": "A questão não corresponde à pergunta atual da partida."})
                    return

                pergunta_partida_id, _, nivel, alternativa_correta = pergunta
                acertou = alternativa_escolhida == alternativa_correta
                pontos = int(round(conta_pontuacao_pergunta(nivel, tempo_segundos))) if acertou else 0
                tempo_registrado = int(round(tempo_segundos))

                cursor.execute("""
                    UPDATE perguntas_partida
                    SET tempo_resposta = %s, acertou = %s, pontos_obtidos = %s
                    WHERE id = %s
                """, (tempo_registrado, acertou, pontos, pergunta_partida_id))

                if acertou:
                    if ordem_atual == 10:
                        cursor.execute("""
                            UPDATE partidas
                            SET pergunta_atual = pergunta_atual + 1,
                                pontuacao = pontuacao + %s,
                                status = 'venceu',
                                data_fim = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (pontos, partida_id))
                    else:
                        cursor.execute("""
                            UPDATE partidas
                            SET pergunta_atual = pergunta_atual + 1,
                                pontuacao = pontuacao + %s
                            WHERE id = %s
                        """, (pontos, partida_id))
                else:
                    cursor.execute("""
                        UPDATE partidas
                        SET status = 'perdeu', data_fim = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (partida_id,))

                conexao.commit()
                self.enviar_resposta(201, {"acertou": acertou, "pontuacao": pontos})

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
            partida_id = dados_recebidos.get("partida_id")
            questao_id = dados_recebidos.get("questao_id")
            tipo_ajuda = dados_recebidos.get("tipo_ajuda")

            tipos_ajuda = {
                "1": "meio_a_meio",
                "2": "pulo",
                "3": "passe_livre",
                "meio_a_meio": "meio_a_meio",
                "pulo": "pulo",
                "passe_livre": "passe_livre",
            }
            tipo_ajuda = tipos_ajuda.get(str(tipo_ajuda))
            if not tipo_ajuda:
                self.enviar_resposta(400, {"erro": "Tipo de ajuda inválido"})
                return

            try:
                partida_id = int(partida_id)
                questao_id = int(questao_id)
            except (TypeError, ValueError):
                self.enviar_resposta(400, {"erro": "Partida ou questão inválida."})
                return
            if partida_id <= 0 or questao_id <= 0:
                self.enviar_resposta(400, {"erro": "Partida ou questão inválida."})
                return

            conexao = None
            cursor = None
            try:
                conexao = self.obter_conexao()
                cursor = conexao.cursor()

                cursor.execute("""
                    SELECT pergunta_atual, status, ajuda_meio_a_meio_usada,
                           ajuda_pulo_usada, ajuda_passe_livre_usada
                    FROM partidas
                    WHERE id = %s
                    FOR UPDATE
                """, (partida_id,))
                partida = cursor.fetchone()
                if not partida:
                    self.enviar_resposta(404, {"erro": "Partida não encontrada."})
                    return

                ordem_atual, status, meio_usada, pulo_usado, passe_usado = partida
                if status != "em_andamento":
                    self.enviar_resposta(409, {"erro": f"Jogo encerrado. Status atual: {status}"})
                    return

                cursor.execute("""
                    SELECT pp.id, pp.questao_id, q.nivel, q.enunciado,
                           q.alt_a, q.alt_b, q.alt_c, q.alt_d, q.alt_correta
                    FROM perguntas_partida pp
                    JOIN questoes q ON q.id = pp.questao_id
                    WHERE pp.partida_id = %s AND pp.ordem = %s
                    ORDER BY pp.id DESC
                    LIMIT 1
                    FOR UPDATE OF pp
                """, (partida_id, ordem_atual))
                pergunta = cursor.fetchone()
                if not pergunta or pergunta[1] != questao_id:
                    self.enviar_resposta(409, {"erro": "A questão não corresponde à pergunta atual da partida."})
                    return

                (pergunta_partida_id, _, nivel, enunciado, alt_a, alt_b,
                 alt_c, alt_d, alternativa_correta) = pergunta
                if tipo_ajuda == "passe_livre" and ordem_atual == 10:
                    self.enviar_resposta(400, {"erro": "O passe livre não pode ser usado na pergunta final."})
                    return

                ajuda_usada = {
                    "meio_a_meio": meio_usada,
                    "pulo": pulo_usado,
                    "passe_livre": passe_usado,
                }[tipo_ajuda]
                if ajuda_usada:
                    self.enviar_resposta(400, {"erro": f"A ajuda '{tipo_ajuda}' já foi utilizada nesta partida."})
                    return

                match tipo_ajuda:
                    case "meio_a_meio":
                        alternativas = {
                            "a": alt_a, "b": alt_b, "c": alt_c, "d": alt_d,
                        }
                        incorretas = [
                            letra for letra in alternativas
                            if letra != alternativa_correta
                        ]
                        eliminadas = sample(incorretas, 2)
                        for letra in eliminadas:
                            alternativas[letra] = ""

                        cursor.execute("""
                            UPDATE partidas SET ajuda_meio_a_meio_usada = TRUE WHERE id = %s
                        """, (partida_id,))
                        cursor.execute("""
                            UPDATE perguntas_partida SET usou_meio_a_meio = TRUE WHERE id = %s
                        """, (pergunta_partida_id,))
                        conexao.commit()
                        self.enviar_resposta(200, {
                            "sucesso": True,
                            "tipo_ajuda": tipo_ajuda,
                            "alternativas": alternativas,
                            "ajudas_disponiveis": {
                                "meio_a_meio": False,
                                "pulo": not pulo_usado,
                                "passe_livre": not passe_usado,
                            },
                        })
                    case "pulo":
                        cursor.execute("""
                            SELECT id, enunciado, alt_a, alt_b, alt_c, alt_d
                            FROM questoes
                            WHERE nivel = %s
                              AND NOT EXISTS (
                                  SELECT 1 FROM perguntas_partida
                                  WHERE partida_id = %s AND questao_id = questoes.id
                              )
                            ORDER BY RANDOM()
                            LIMIT 1
                        """, (nivel, partida_id))
                        nova_pergunta = cursor.fetchone()
                        if not nova_pergunta:
                            conexao.rollback()
                            self.enviar_resposta(409, {
                                "erro": f"Não há outra questão disponível do nível '{nivel}'."
                            })
                            return

                        nova_questao_id, novo_enunciado, nova_alt_a, nova_alt_b, nova_alt_c, nova_alt_d = nova_pergunta
                        cursor.execute("""
                            UPDATE partidas SET ajuda_pulo_usada = TRUE WHERE id = %s
                        """, (partida_id,))
                        cursor.execute("""
                            UPDATE perguntas_partida
                            SET usou_pulo = TRUE, acertou = FALSE,
                                tempo_resposta = 0, pontos_obtidos = 0
                            WHERE id = %s
                        """, (pergunta_partida_id,))
                        cursor.execute("""
                            INSERT INTO perguntas_partida (partida_id, questao_id, ordem)
                            VALUES (%s, %s, %s)
                        """, (partida_id, nova_questao_id, ordem_atual))
                        conexao.commit()
                        self.enviar_resposta(200, {
                            "sucesso": True,
                            "tipo_ajuda": tipo_ajuda,
                            "questao_id": nova_questao_id,
                            "ordem": ordem_atual,
                            "nivel": nivel,
                            "enunciado": novo_enunciado,
                            "alternativas": {
                                "a": nova_alt_a, "b": nova_alt_b,
                                "c": nova_alt_c, "d": nova_alt_d,
                            },
                            "ajudas_disponiveis": {
                                "meio_a_meio": not meio_usada,
                                "pulo": False,
                                "passe_livre": not passe_usado,
                            },
                        })
                    case "passe_livre":
                        pontos = int(round(conta_pontuacao_pergunta(nivel, 60)))
                        cursor.execute("""
                            UPDATE partidas
                            SET ajuda_passe_livre_usada = TRUE,
                                pontuacao = pontuacao + %s,
                                pergunta_atual = pergunta_atual + 1
                            WHERE id = %s
                        """, (pontos, partida_id))
                        cursor.execute("""
                            UPDATE perguntas_partida
                            SET usou_passe_livre = TRUE, acertou = TRUE,
                                tempo_resposta = 0, pontos_obtidos = %s
                            WHERE id = %s
                        """, (pontos, pergunta_partida_id))
                        conexao.commit()
                        self.enviar_resposta(200, {
                            "sucesso": True,
                            "tipo_ajuda": tipo_ajuda,
                            "avancou": True,
                            "pontuacao": pontos,
                            "ajudas_disponiveis": {
                                "meio_a_meio": not meio_usada,
                                "pulo": not pulo_usado,
                                "passe_livre": False,
                            },
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

        else:
            self.enviar_resposta(404, {"erro": "Rota POST nao encontrada"})


    def enviar_resposta(self, codigo, resposta):
        conteudo = json.dumps(resposta).encode('utf-8')

        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", f"{len(conteudo)}")
        self.end_headers()

        self.wfile.write(conteudo)

def conta_pontuacao_pergunta(nivel, tempo):
    """Contabiliza quantos pontos a questão resultou"""
    pontuacoes_base = {
        "facil": (50, 1),
        "medio": (100, 1.5),
        "dificil": (300, 2),
        "final": (1000, 10),
    }
    if nivel not in pontuacoes_base:
        raise ValueError(f"Nível de questão inválido: {nivel}")
    base, fator = pontuacoes_base[nivel]
    pontuacao = base + max(0, 60 - tempo) * fator
    return math.floor(pontuacao + 0.5)


if __name__ == "__main__":
    # Configuração do parser de argumentos da CLI
    parser = argparse.ArgumentParser(description="Nó Servidor REST do Quiz Online")
    parser.add_argument("-p", "--porta", type=int, default=8000, help="Porta de execução do servidor (padrão: 8000)")
    
    args = parser.parse_args()
    porta_escolhida = args.porta

    servidor = ThreadingHTTPServer((ENDERECO, porta_escolhida), ServidorREST)
    servidor.daemon_threads = True
    print(f"Servidor REST (Nó Servidor) iniciado em {ENDERECO}:{porta_escolhida}, aguardando requisições...")
    
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor de forma segura...")
        servidor.server_close()