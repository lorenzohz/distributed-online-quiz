# Trabalho Prático - Sistemas Distribuídos

## Quiz Online

Projeto desenvolvido para a disciplina de Sistemas Distribuídos pelos alunos:

- Caetano Vendrame Mantovani (RA: 135846)
- Lorenzo Henrique Zanetti (RA: 133076)
- Vitor da Rocha Machado (RA: 132769)

Este projeto é uma aplicação em Python para um jogo de perguntas e respostas com arquitetura distribuída (REST), banco de dados PostgreSQL e balanceamento de carga HTTP.

## Requisitos

- Python 3.10+
- PostgreSQL 15 (executado via Docker)
- Docker e Docker Compose
- Bibliotecas Python listadas em `requirements.txt`

## Dependências adicionais

As bibliotecas externas necessárias são:

- `psycopg2` — conexão com PostgreSQL
- `python-dotenv` — leitura do arquivo `.env`
- `requests` — chamadas HTTP no cliente

Essas dependências podem ser instaladas com:

```bash
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuração do ambiente

1. Crie o arquivo `.env` na raiz do projeto a partir do exemplo:

```bash
copy .env.example .env
```

2. Preencha a senha do banco no arquivo `.env`:

```env
DB_PASSWORD=sua_senha
```

3. Suba o banco PostgreSQL (com Docker Desktop rodando em segundo plano):

```bash
docker compose up -d
```

4. Caso ocorra algum problema quanto ao acesso correto dos dados no BD, a porta utilizada pelo Docker e pelo PostgreSQl é a mesma. Então possivelmente o PostgreSQL rodando em plano de fundo deverá ser fechado:

```bash
# Retirando o BD local para o pipeline utilizar o Docker corretamente:
win + r
services.msc
OK
postgresql-x64-... (botão direito -> Parar)
# Depois, no terminal do projeto:
docker compose down -v
docker compose up -d db
```

## Como executar

Não há etapa de compilação, pois o projeto é escrito em Python e executado diretamente.

### 1) Iniciar os servidores da aplicação

Em terminais separados, execute:

```bash
python server.py -p 8001
python server.py -p 8002
python server.py -p 8003
```

### 2) Iniciar o balanceador de carga

Em outro terminal:

```bash
python balanceador.py
```

O balanceador encaminha requisições para os nós em `127.0.0.1:8001`, `127.0.0.1:8002` e `127.0.0.1:8003`.

### 3) Executar o cliente

Em um terminal adicional:

```bash
python client.py
```

O cliente acessa o serviço pela URL padrão:

```text
http://127.0.0.1:8000
```

## Estrutura principal do projeto

- `server.py` — servidor REST da aplicação
- `client.py` — cliente interativo do jogo
- `balanceador.py` — balanceador HTTP round-robin
- `docker-compose.yml` — configuração do PostgreSQL
- `scripts/criar_banco.sql` — criação do banco
- `scripts/popular_banco.py` — inserção das perguntas
- `requirements.txt` — dependências do projeto

## Observações

- O projeto pode ser executado em modo local sem compilação.
- O banco utilizado é PostgreSQL e deve estar disponível antes do uso do sistema.
- O cliente usa a variável de ambiente `QUIZ_SERVICE_URL` quando definida; caso não exista, assume `http://127.0.0.1:8000`.
