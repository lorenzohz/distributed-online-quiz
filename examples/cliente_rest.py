from urllib.request import urlopen
from urllib.parse import urlencode
import json

ENDERECO = "127.0.0.1" #localhost
PORTA= "8000"

# formato = http://[endereco]:[porta]/[operação]?[parametros]

while True:

    print("--- Realizando operações matemáticas elementares com REST")
    print("1 - Somar")
    print("2 - Multiplicar")
    print("3 - Subtrair")
    print("4 - Dividir")
    print("0 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "0":
        break

    if opcao in ["1", "2", "3", "4"]:

        try:
            a = float(input("Digite o primeiro número: "))
            b = float(input("Digite o segundo número: "))

    
            if opcao == "1":
                operacao = "somar"
            elif opcao == "2":
                operacao = "multiplicar"
            elif opcao == "3":
                operacao = "subtrair" 
            elif opcao == "4":
                operacao = "dividir"

            # formato = http://[endereco]:[porta]/[operação]?[parametros]

            parametros = urlencode({
                                    "a": a,
                                    "b": b
                                    })
            
            url = f"http://{ENDERECO}:{PORTA}/{operacao}?{parametros}"
            
            # espera a resposta, portanto é comunicação síncrona
            resultado = urlopen(url)

            conteudo = json.loads(resultado.read())
            print(f"Resultado: {conteudo["resultado"]}")
            _ = input("Pressione uma tecla para continuar!")
            print("\n\n\n")

        except Exception as erro:
            print("Erro ao comunicar com o servidor:")
            print(erro)

    else:
        print("Opção inválida.")
