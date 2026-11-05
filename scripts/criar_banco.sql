-- 1. Tabela de Questões
CREATE TABLE questoes (
    id SERIAL PRIMARY KEY,
    nivel VARCHAR(10), -- Ex: 'facil', 'medio', 'dificil', 'final'
    enunciado TEXT,
    alt_a TEXT,
    alt_b TEXT,
    alt_c TEXT,
    alt_d TEXT,
    alt_correta VARCHAR(1) -- Ex: 'a', 'b', 'c', 'd'
);

-- 2. Tabela de Partidas (Sessão do Jogador)
CREATE TABLE partidas (
    id SERIAL PRIMARY KEY,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    pergunta_atual INT DEFAULT 1,
    pontuacao INT DEFAULT 0,
    ajuda_meio_a_meio_usada BOOLEAN DEFAULT FALSE,
    ajuda_pulo_usada BOOLEAN DEFAULT FALSE,
    ajuda_passe_livre_usada BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'em_andamento',
    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fim TIMESTAMP
);

-- 3. Tabela de Junção/Histórico
CREATE TABLE perguntas_partida (
    id SERIAL PRIMARY KEY,
    partida_id INT REFERENCES partidas(id) ON DELETE CASCADE,
    questao_id INT REFERENCES questoes(id) ON DELETE CASCADE,
    ordem INT,
    tempo_resposta INT,
    acertou BOOLEAN,
    pontos_obtidos INT DEFAULT 0,
    usou_meio_a_meio BOOLEAN DEFAULT FALSE,
    usou_pulo BOOLEAN DEFAULT FALSE,
    usou_passe_livre BOOLEAN DEFAULT FALSE
);