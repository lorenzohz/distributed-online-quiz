import json
import requests
import time

SERVICO_URL = "http://127.0.0.1:8000"

# formato = http://[endereco]:[porta]/[operação]?[parametros]
# Conexão deve ser realizada para o Balanceador de Carga

'''
Telas Necessárias:
3. Iniciar um novo jogo -> Solicitar Nickname
4.1. Tela das perguntas
4.2. Solicitar ajuda -> Escolher ajuda
5. Fim de Jogo vitória
6. Fim de Jogo derrota
7. Transição (3 segundos de preparação)
'''

'''
inicio -> ranking, iniciar
iniciar -> nickname -> transição -> pergunta
pergunta -> (ajuda -> escolher ajuda -> volta pra pergunta) | (responder certo -> transicao -> proxima pergunta) | (responder errado -> derrota)
pergunta final -> (responder certo -> fim de jogo vitória) | (responder errado -> derrota)
fim de jogo/derrota -> inicio
'''

# Dados Mock:
def __get_ranking():
    return json.dumps({
        "ranking": [
            {"nickname": "Shadow", "pontuacao": 1500},
            {"nickname": "Ninja", "pontuacao": 1350},
            {"nickname": "Pixel", "pontuacao": 1200},
            {"nickname": "GamerX", "pontuacao": 1100},
            {"nickname": "Zero", "pontuacao": 980},
            {"nickname": "Luna", "pontuacao": 850},
            {"nickname": "Cyber", "pontuacao": 720},
            {"nickname": "Ghost", "pontuacao": 600},
            {"nickname": "Raven", "pontuacao": 450},
            {"nickname": "Player10", "pontuacao": 300}
        ]
    })


def cliente():
    "Implementa a lógica do jogo de perguntas no lado do cliente"
    estado = 'inicio'
    pontuacao = 0

    while True:
        if estado == 'inicio':
            estado = tela_inicial()

        elif estado == 'ranking':
            estado = ranking()

        elif estado == 'perguntas':
            codigo, dado = nickname()
            if codigo == 2: # Erro
                input("\n\nPressione Enter para voltar à Tela Inicial ")
                estado = 'inicio'

            elif codigo == 1:
                pass
            
            elif codigo == 0:
                resultado, pontos = ciclo_perguntas(dado)
                pontuacao = pontos
                if resultado == 2: # Erro
                    input("\n\nPressione Enter para voltar à Tela Inicial ")
                    estado = 'inicio'

                elif resultado == 1:
                    estado = 'vitoria'

                elif resultado == 0:
                    estado = 'derrota'

                else:
                    raise ValueError("Estado inválido! Finalizando\n")

            else:
                raise ValueError("Estado inválido! Finalizando\n")
                

        elif estado == 'vitoria':
            fim_vitoria(pontuacao)
            input("\n\nPressione Enter para voltar à Tela Inicial ")
            print("\n\n\n\n\n")
            estado = 'inicio'

        elif estado == 'derrota':
            fim_derrota(pontuacao)
            input("\n\nPressione Enter para voltar à Tela Inicial ")
            print("\n\n\n\n\n")
            estado = 'inicio'
            
        elif estado == 'sair':
            print("Obrigado por participar do jogo!")
            break

        else:
            raise ValueError("Estado inválido! Finalizando\n")


def tela_inicial():
    """Implementa o estado correspondente à tela inicial"""

    print("""               
               @@@@@@@@@@@           
           @@@@@@         @@@@          Trabalho Prático - Sistemas Distribuídos
         @@@ @@@@            @@@        Quiz Online - Twenty One Pilots
       @@@   @@@@              @@@      
     @@@     @@@@         @@@@@  @@@    Alunos:
     @@      @@@@        @@@@@    @@    - Caetano Vendrame Mantovani (RA: 135846)
    @@@      @@@@ @@@@@ @@@@@     @@@   - Lorenzo Henrique Zanetti (RA: 133076)
     @@      @@@@      @@@@@      @@    - Vitor da Rocha Machado (RA: 132769)
     @@@     @@@@     @@@@@      @@@    
       @@@   @@@@              @@@      Selecione uma opção digitando no terminal:
         @@@ @@@@            @@@        [1] Novo Jogo
           @@@@@@         @@@@          [2] Exibir Ranking
               @@@@@@@@@@@              [3] Sair do Quiz 
    
    """)

    opcao = '0'
    while not opcao in ('1', '2', '3'):
        opcao = input("Opção: ")

        if opcao == '1': # Novo jogo
            return 'perguntas'

        elif opcao == '2': # Exibir Ranking
            return 'ranking'

        elif opcao == '3': # Sair do Quiz
            return 'sair'


def ranking():
    """Implementa o estado correspondente à tela com o ranking de pontuação"""

    # ranking = json.loads(__get_ranking())["ranking"] // Mock
    url = f"{SERVICO_URL}/ranking"

    try:
        resposta = requests.get(url, timeout=10)

        if resposta.status_code == 200:
            dados = resposta.json()
            ranking = dados.get("ranking", [])
    
            print("\n")
            print(" " * 23 + "|-/ Ranking |-/")
        
            print(f"{'Pos.':<7} {'Nickname':<50} {'Pontos':>6}")
            print("-" * 66)
        
            for i, jog in enumerate(ranking[:10], start=1):
                nickname = jog["nickname"][:50]
                pontuacao = jog["pontuacao"]
        
                print(f"{i:02}º     {nickname:<50} {pontuacao:>6}")
        
            print(" " * 25 + "|-/ |-/ |-/")

        elif resposta.status_code == 500:
            print(f"\nErro no servidor: {dados.get('erro')}")

        else:
            print(f"\nErro desconhecido: {resposta.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"\nFalha de conexão: Não foi possível conectar ao servidor em {SERVICO_URL}.")

    except Exception as e:
        print(f"Erro inesperado: {e}")

    input("\nAperte Enter para voltar ao início ")
    print("\n" * 5)

    return 'inicio' # Voltar para a tela inicial


def nickname():
    """Define nickname para um novo jogo"""
    
    nickname = input("Digite o seu nickname: ").strip()
    if not nickname or len(nickname) > 50:
        print("\nNickname inválido!")
        return 1, None # Nickname inválido

    url = f"{SERVICO_URL}/partida"
    payload = {"nickname": nickname}

    try:
        resposta = requests.post(url, json=payload, timeout=10)

        if resposta.status_code == 201:
            dados = resposta.json()
            return 0, dados.get("partida_id") # Sucesso

        elif resposta.status_code == 400:
            dados = resposta.json()
            print(f"\nErro de lógica: {dados.get('erro')}")
            return 1, None # Nickname repetido ou inválido

        elif resposta.status_code == 500:
            dados = resposta.json()
            print(f"\nErro no servidor: {dados.get('erro')}")
            return 2, None

        else:
            print(f"\nErro desconhecido: {resposta.status_code}")
            return 2, None

    except requests.exceptions.ConnectionError:
        print(f"\nFalha de conexão: Não foi possível conectar ao servidor em {SERVICO_URL}.")
        return 2, None

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return 2, None


def ciclo_perguntas(partida_id):
    """Implementa a partida realizando o ciclo de perguntas ao usuário"""
    url_pergunta = f"{SERVICO_URL}/pergunta?partida_id={partida_id}" # Get
    url_resposta = f"{SERVICO_URL}/responder?partida_id={partida_id}" # Post
    url_ajuda = f"{SERVICO_URL}/ajuda?partida_id={partida_id}" # Post
    
    nivel = 1
    acertou = True
    alternativas = {}
    ajudas = {}
    pontuacao = 0

    __delay(mensagem=f"\nIniciando partida!", tempo=5)
    while nivel < 10:
        codigo, dados = obter_pergunta(url_pergunta)
        if codigo == 1:
            return 2, pontuacao
        
        nivel = dados["ordem"]
        enunciado = dados["enunciado"]

        alternativas['a'] = dados["alternativas"]["a"]
        alternativas['b'] = dados["alternativas"]["b"]
        alternativas['c'] = dados["alternativas"]["c"]
        alternativas['d'] = dados["alternativas"]["d"]

        ajudas["meio_a_meio"] = dados["ajudas_disponiveis"]["meio_a_meio"]
        ajudas["pulo"] = dados["ajudas_disponiveis"]["pulo"]
        ajudas["passe_livre"] = dados["ajudas_disponiveis"]["passe_livre"]

        tempo_inicio = time.perf_counter()
        respondida = False
        while not respondida:
            opcao = realizar_pergunta(nivel, enunciado, alternativas, ajudas)
            if opcao in ('1', '2', '3'):
                print("\nImplementar lógica de ajuda")

            elif opcao in ('a', 'b', 'c', 'd'):
                print("\nImplementar lógica de resposta")
                respondida = True
                acertou = opcao == 'a'

            else:
                return 2, pontuacao

        if acertou:
            tempo_final = time.perf_counter()
            novos_pontos = __conta_pontuacao_pergunta(nivel, tempo_final - tempo_inicio)
            pontuacao += novos_pontos
            print(f"\nCerta Resposta! Você ganhou {novos_pontos:.3f} pontos! |-/".replace('.', ','))
            if nivel < 10:
                __delay(mensagem=f"Pontuação Atual: {pontuacao:.3f} pontos!\n\nPrepare-se!".replace('.', ','),tempo=5)
            if nivel == 10:
                __delay(tempo=3)
                return 1, pontuacao

        else:
            print(f"\nResposta Errada!")
            __delay(mensagem="Finalizando jogo", tempo=3)
            return 0, pontuacao

def obter_pergunta(url_pergunta):
    """Realiza a obtenção da pergunta atual para a partida no servidor"""
    try:
        resposta = requests.get(url_pergunta, timeout=10)

        if resposta.status_code == 200:
            dados = resposta.json()
            return 0, dados

        elif resposta.status_code == 400:
            dados = resposta.json()
            print(f"\nErro de lógica: {dados.get('erro')}")
            return 1, dados
        
        elif resposta.status_code == 404:
            dados = resposta.json()
            print(f"\nFonte não encontrada: {dados.get('erro')}")
            return 1, dados
        
        elif resposta.status_code == 500:
            dados = resposta.json()
            print(f"\nErro no servidor: {dados.get('erro')}")
            return 1, dados

        else:
            print(f"\nErro desconhecido: {resposta.status_code}")
            return 1, resposta

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return 1, resposta


def realizar_pergunta(nivel, enunciado, alternativas, ajudas):
    """Imprime as opções disponíveis na resposta da pergunta e captura a escolha do usuário"""
    if nivel < 4:
        c = 'Ψ'
    elif nivel < 7:
        c = '✺'
    elif nivel < 10:
        c = '⊬'
    else:
        c = 'ғ̶ᴘ̶ᴇ̶'

    escolhas = []

    print(f"\n{c} Pergunta {nivel}: {enunciado}")
    for alt in alternativas.keys():
        if alternativas[alt] != "":
            escolhas.append(alt)
            print(f"{alt}) {alternativas[alt]}")

    i = 1
    print("\nAjudas Disponíveis:")
    for aju in ajudas.keys():
        if ajudas[aju]:
            escolhas.append(str(i))
            print(f"{i} - {__formata_ajuda(aju)}")
        i += 1

    escolhas_txt = " ".join(escolhas)
    opcao = input(f"\nDigite a sua escolha {escolhas_txt}: ").strip()[0]
    while not opcao in escolhas:
        print("Escolha inválida!")
        opcao = input(f"Digite a sua escolha {escolhas_txt}: ").strip()[0]
    
    return opcao


def fim_vitoria(pontuacao):
    """Imprime a tela de fim de jogo no caso de vitória do jogador"""
    pontuacao_str = f"{pontuacao:.3f}".replace('.', ',')
    print(f"""                                                
                        $$.     . " .     .$$
                       $ ./$$$$$$$$$$$$$$$\. $
                      q.   ^$$$$$$$$$$$$$^   .p
$$$$$              I$$$$n $$$$$$$$$$$$$$$$$ n$$$$I              $$$$$
$$.$$$$$$^.   o$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$o   .^$$$$$$.$$
$$. . $$$$$$$$$$$#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#$$$$$$$$$$$ . .$$
@$.b$$$$-. .. /I$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$I\ .. .-$$$$d.$@
 $$ $$$$$$$$$$$.$$$$$$$    `$$$$$$$$$$$$$'    $$$$$$$.$$$$$$$$$$$ $$
  $$ B$$$$$$$$.$$$$$$$       j$$$$$$$$$l       $$$$$$$.$$$$$$$$B $$
    $c.$$$$$$ $$$$$$$$       q0$$$$$$$0p       $$$$$$$$ $$$$$$.c$
      [$'M$$$ $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ $$$M'$]
           .  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$  .
              .$$$$$$$$$$$$$$$$v     v$$$$$$$$$$$$$$$$.
               .$$$W$$$$$$$$$$$$$$.$$$$$$$$$$$$$$W$$$.
                 $$$.$$$$$$$$$$$$$.$$$$$$$$$$$$$.$$$
                    .`$$q   ..   [.]   ..   p$$'.       Ned está orgulhoso! |-/
                        ^$$$$$$$$v&v$$$$$$$$^           Parabéns pela vitória!
                           .:$$$$$$$$$$$:.              Pontuação Final: {pontuacao_str} Pontos.replace('.', ',')
""")


def fim_derrota(pontuacao):
    """Imprime a tela de fim de jogo no caso de derrota do jogador"""
    pontuacao_str = f"{pontuacao:.3f}".replace('.', ',')
    print(f"""                                                
                    @@@@@@@@@@@@@@@@@
              @@@@                     @@@@
           @@@       @@@@@@@ @@@@@@@       @@@
         @@    @@@@  @@@@@@@ @@@@@@@  @@@@    @@
        @    @@@@@@@  @@@@     @@@@  @@@@@@@    @
      @   @@@ @@@@@@   @@@@   @@@@   @@@@@@ @@@   @
    @@  @@@@@@    @@@   @@@@ @@@@   @@@    @@@@@@  @@
   @@  @@@@@@@    @@@@  @@@@ @@@@  @@@@    @@@@@@@  @@
  @       @@@ @@@@ @@@@           @@@@ @@@@ @@@       @
 @@  @@@@@    @@@@@@                 @@@@@@    @@@@@  @@
 @  @@@@@@@     @@                     @@     @@@@@@@  @
 @  @@@@@@ @@@@@@                       @@@@@@ @@@@@@  @
@  @@@@@    @@@@       @@@ @@@ @@@       @@@@    @@@@@  @
@  @@@@@    @@@@                         @@@@    @@@@@  @
@  @@@@@@ @@@@@@       @@@ @@@ @@@       @@@@@@ @@@@@@  @
@  @@@@@@                                       @@@@@@  @
@         @@@@@@       @@@ @@@ @@@       @@@@@@         @
 @  @@@@@@ @@@@@@                       @@@@@@ @@@@@@  @
 @  @@@@@@    @@@@                     @@@@    @@@@@@  @
 @@  @@@@@    @@@@@@                 @@@@@@    @@@@@  @@
  @   @@@@@@  @@   @@@@           @@@@   @@  @@@@@@   @
   @@  @@@@@@@    @@@@@ @@@@ @@@@ @@@@@    @@@@@@@  @@
    @@   @@@@@   @@@   @@@@@ @@@@@   @@@   @@@@@   @@
      @    @   @@@@@    @@@@ @@@@    @@@@@   @    @
        @    @@@@@@@  @@@@@@ @@@@@@  @@@@@@@    @
         @@     @@@@ @@@@@@@ @@@@@@@ @@@@     @@    Dessa vez, Dema vence /-|
           @@@      @@@@@@@@ @@@@@@@@      @@@      Continuaremos seguindo...
              @@@@                     @@@@         Pontuação Final: {pontuacao_str} Pontos
                    @@@@@@@@@@@@@@@@@
""")

def __formata_ajuda(chave):
    """Realiza a formatação correta da ajuda nas opções das perguntas"""
    formatado = "Desconhecido"
    if chave == "meio_a_meio":
        formatado = "Eliminar duas alternativas erradas"
    elif chave == "pulo":
        formatado = "Pular questão"
    elif chave == "passe_livre":
        formatado = "Acertar questão (sem bônus)"
    return formatado


def __conta_pontuacao_pergunta(nivel, tempo):
    """Contabiliza quantos pontos a questão resultou"""
    if nivel < 4:
        pontos = 50
        fator = 1
    elif nivel < 7:
        pontos = 100
        fator = 1.5
    elif nivel < 10:
        pontos = 300
        fator = 2
    elif nivel == 10:
        pontos = 1000
        fator = 10

    return round(pontos + max(0, (60 - tempo)) * fator, 3)

def __delay(mensagem=None, tempo=3):
    """Rotina que aplica pausas com contagem para a transição de estados"""
    if mensagem:
        print(mensagem)
    
    for i in range(tempo, 0, -1):
        print(i)
        time.sleep(1)

if __name__ == "__main__":
    cliente()