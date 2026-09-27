import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# 1. Resolver o caminho do ficheiro .env
# __file__ aponta para este script.
# .parent.parent sobe dois níveis: sai do ficheiro e sai da pasta 'postgres_scripts'
caminho_env = Path(__file__).resolve().parent.parent / '.env'

# Carregar as variáveis de ambiente
load_dotenv(dotenv_path=caminho_env)

# Capturar a palavra-passe
senha_banco = os.getenv("DB_PASSWORD")

if not senha_banco:
    raise ValueError("A senha do banco não foi encontrada. Verifique o ficheiro .env.")

# Dados das perguntas omitidos por brevidade (mantenha a sua lista de tuplos aqui)
perguntas = [
    # Nível Fácil (Exemplos)
    (
        'facil', 
        'Qual é o nome do vocalista e principal compositor dos Twenty One Pilots?', 
        'Josh Dun', 
        'Tyler Joseph', 
        'Gerard Way', 
        'Brendon Urie', 
        'b'
    ),
    (
        'facil', 
        'Qual destes instrumentos é a marca registada de Josh Dun nos concertos?', 
        'Baixo', 
        'Teclado', 
        'Bateria', 
        'Ukulele', 
        'c'
    ),
    
    # Nível Médio (Exemplos)
    (
        'medio', 
        'Em que ano foi lançado o álbum "Blurryface", que catapultou a banda para o sucesso global?', 
        '2013', 
        '2015', 
        '2017', 
        '2018', 
        'b'
    ),
    (
        'medio', 
        'Qual é o nome da mascote (uma criatura adorável com chifres) que aparece no videoclipe de "Chlorine"?', 
        'Ned', 
        'Trash', 
        'Clancy', 
        'Nico', 
        'a'
    ),

    # Nível Difícil (Exemplos)
    (
        'dificil', 
        'Na "lore" (história fictícia) criada pela banda, como se chama a cidade opressiva governada por nove bispos?', 
        'Trench', 
        'Voldsoy', 
        'Dema', 
        'Paladin Strait', 
        'c'
    ),
    (
        'dificil', 
        'Qual foi o primeiro baterista da banda, antes de Josh Dun se juntar a Tyler Joseph?', 
        'Chris Salih', 
        'Nick Thomas', 
        'Mark Eschleman', 
        'Zack Joseph', 
        'a'
    ),

    # Nível Final (Exemplos)
    (
        'final', 
        'Qual é a faixa de abertura do álbum de estreia independente e homónimo da banda, lançado em 2009?', 
        'Fall Away', 
        'Implicit Demand for Proof', 
        'The Pantaloon', 
        'Addict With A Pen', 
        'b'
    )
]

def popular_base_dados():
    try:
        # 2. Utilizar a senha carregada na conexão
        conexao = psycopg2.connect(
            dbname="quiz_online",
            user="postgres",
            password=senha_banco, 
            host="localhost",
            port="5432"
        )
        cursor = conexao.cursor()

        query_insercao = """
            INSERT INTO questoes (nivel, enunciado, alt_a, alt_b, alt_c, alt_d, alt_correta)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        print("A iniciar a inserção de perguntas...")
        for pergunta in perguntas:
            cursor.execute(query_insercao, pergunta)
            
        conexao.commit()
        print(f"Sucesso: {len(perguntas)} perguntas foram inseridas na base de dados!")

    except psycopg2.Error as e:
        print(f"Erro ao interagir com a base de dados: {e}")
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexao' in locals():
            conexao.close()
            print("Ligação à base de dados encerrada.")

if __name__ == "__main__":
    popular_base_dados()