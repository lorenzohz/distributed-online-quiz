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

-- 4. Inserir perguntas
INSERT INTO questoes (nivel, enunciado, alt_a, alt_b, alt_c, alt_d, alt_correta) VALUES
('facil', 'Qual é o nome dos dois maiores singles da banda?', 'Chlorine e Ride', 'Stressed Out e Ride', 'Tear in My Heart e Heathens', 'Heathens e Stressed Out', 'b'),
('facil', 'Qual música produzida pela banda foi utilizada na trilha sonora do filme Esquadrão Suicida?', 'Heathens', 'Sucker for Pain', 'The Line', 'Stressed Out', 'a'),
('facil', 'Qual música produzida pela banda foi utilizada na trilha sonora da série Arcane, da Netflix?', 'Next Semester', 'Enemy', 'Heathens', 'The Line', 'd'),
('facil', 'Qual é o nome do atual baterista da banda?', 'Josh Dun', 'Daniel Platzman', 'Bob Bryar', 'Brett Kramer', 'a'),
('facil', 'Qual é o nome do cantor principal da banda?', 'Dan Reynolds', 'Tyler Joseph', 'Chris Martin', 'Josh Taylor', 'b'),
('facil', 'Qual álbum da banda ilustra em sua capa um abutre?', 'Blurryface', 'Scaled And Icy', 'Trench', 'Clancy', 'c'),
('facil', 'Qual álbum da banda ilustra em sua capa os avôs de seus integrantes?', 'Breach', 'Regional at Best', 'Vessel', 'Blurryface', 'c'),
('facil', 'Atualmente, a banda é formada por quantos integrantes?', 'Dois', 'Quatro', 'Vinte e um', 'Três', 'a'),
('facil', 'Quais elementos visuais caracterizaram predominantemente os logos da banda ao longo dos anos?', 'Três linhas horizontais uma em cima da outra', 'As letras “F”, “P” e “E” riscadas', 'Uma linha vertical e uma diagonal, separadas por uma horizontal', 'Os números “dois” e “um” dentro de um círculo', 'c'),
('facil', 'Em qual ano o álbum Blurryface, contendo músicas como Stressed Out e Ride, foi lançado?', '2019', '2015', '2013', '2017', 'b'),
('facil', 'Em qual festival no Brasil a banda foi headliner em 2026?', 'GPWeek', 'Lollapalooza', 'The Town', 'Rock in Rio', 'd'),
('facil', 'Qual é o nome do primeiro álbum produzido pela banda?', 'Blurryface', 'Vessel', 'Endless', 'Twenty One Pilots', 'd'),

('medio', 'Quantos Grammy Awards a banda conquistou?', '9', '1', '7', '3', 'b'),
('medio', 'Em qual cidade a banda se originou?', 'Columbus, Ohio', 'Yonkers, New York', 'Los Angeles, California', 'Philadelphia, Pennsylvania', 'a'),
('medio', 'Qual é a cor representativa dos Banditos na simbologia da banda?', 'Vermelho', 'Azul', 'Rosa', 'Amarelo', 'd'),
('medio', 'O que o personagem Blurryface representa na simbologia da banda?', 'A resistência em função da luta pela saúde mental', 'Os fãs que acompanham a banda ao longo da história', 'Uma personificação das inseguranças e da depressão', 'A imaginação e a liberdade criativa do cantor', 'c'),
('medio', 'Com qual música a banda convencionalmente encerra os seus shows?', 'Tally', 'Leave The City', 'The Judge', 'Trees', 'd'),
('medio', 'Como é o nome da base de fãs que acompanha a banda?', 'Firebreathers', 'Army', 'Clique', 'Twenties', 'c'),
('medio', 'Qual destas músicas não faz parte do álbum autointitulado Twenty One Pilots?', 'Car Radio', 'Trapdoor', 'Johnny Boy', 'Fall Away', 'a'),
('medio', 'Qual música foi lançada na edição limitada do álbum Breach, Digital Remains, que não esteve na versão padrão?', 'Level of Concern', 'Drag Path', 'Drown', 'The Craving', 'b'),
('medio', 'Qual destas músicas fez parte do álbum Regional at Best?', 'The Pantaloon', 'Ruby', 'Routines In The Night', 'The Wolf', 'b'),
('medio', 'Qual destas músicas não possui um ukulele em seu instrumental?', 'We Don’t Believe What’s On TV', 'Next Semester', 'Tally', 'House of Gold', 'c'),
('medio', 'O personagem Ned teve sua primeira aparição no clipe de qual música?', 'Level of Concern', 'The Outside', 'The Hype', 'Chlorine', 'd'),
('medio', 'Como os integrantes da banda receberam o seu Grammy Award em 2017?', 'Vestindo cueca sem calças', 'Vestindo ternos', 'Vestindo fantasias', 'Usando perucas', 'a'),

('dificil', 'Com qual gravadora norte-americana a banda assinou contrato em 2012?', 'Atlantic Records', 'Capitol Records', 'Fueled by Ramen', 'Interscope Records', 'c'),
('dificil', 'Qual destas músicas fez parte do álbum Regional at Best e foi lançada novamente no álbum Vessel?', 'Ode to Sleep', 'Ruby', 'Saturday', 'Fake You Out', 'a'),
('dificil', 'De acordo com a narrativa explorada pela banda, qual destes nomes não é o nome de um dos bispos de Dema?', 'Inter', 'Andre', 'Sacarver', 'Nico', 'a'),
('dificil', 'De acordo com a narrativa explorada pela banda, o que o Vialismo preconiza?', 'A construção de uma sociedade baseada na união', 'A autodestruição como o único caminho para o paraíso', 'Alcançar a felicidade por meio da liberdade individual', 'A rejeição da música como forma de expressão', 'b'),
('dificil', 'A invasão dos Banditos à cidade de Dema durante a guerra se inicia no clipe de qual música?', 'Heavydirtysoul', 'My Blood', 'Paladin Strait', 'Holding On To You', 'c'),
('dificil', 'Quais integrantes da banda a deixaram em 2011?', 'Oliver Sykes e Gabriel Jacoby', 'Nick Thomas e Chris Salih', 'Julian Casablancas e Albert Hammond Jr.', 'John Visa e Matt William', 'b'),
('dificil', 'De acordo com a narrativa explorada pela banda, o que é o ato de seizing?', 'Apagar as memórias', 'Controlar um cadáver', 'Controlar os pensamentos', 'Aprisionar uma alma', 'b'),
('dificil', 'De acordo com a narrativa explorada pela banda, em qual ilha Clancy se encontra após naufragar durante os eventos no clipe da música Saturday?', 'Trench', 'Glorious Vista', 'Paladin Strait', 'Voldsoy', 'd'),
('dificil', 'A turnê intitulada Takeover Tour foi produzida pela banda em suporte a qual de seus álbuns?', 'Clancy', 'Vessel', 'Trench', 'Scaled and Icy', 'd'),
('dificil', 'Qual é o nome do dragão ilustrado na capa do álbum Scaled and Icy?', 'Trash', 'Clancy', 'Nico', 'Ned', 'a'),
('dificil', 'Qual destes clipes não ilustra a banda performando um concerto a um público?', 'The Hype', 'Car Radio', 'Doubt (Demo)', 'The Contract', 'd'),
('dificil', 'Qual destes símbolos não faz parte da capa do álbum Trench?', 'Um abutre', 'Um selo FPE', 'Uma lâmpada', 'Um tridente', 'c'),

('final', 'Qual é a origem do nome da banda Twenty One Pilots?', 'Um livro de poemas', 'Uma peça de teatro', 'Uma novela romântica', 'Uma pintura clássica', 'b'),
('final', 'De acordo com a narrativa explorada pela banda, qual é o nome do bispo que era responsável por Clancy?', 'Nills', 'Keons', 'Vetomo', 'Listo', 'b'),
('final', 'Quantos códigos havia no evento ARG produzido pela banda em 2020?', '20', '15', '18', '25', 'a'),
('final', 'O clipe da música Drag Path é originado de qual vídeo?', 'Magic Night', 'Bunny Run', 'The Skeleton Fight', 'Out of a Forest', 'd'),
('final', 'O bispo chamado Lisden possui esse nome a partir de trechos de qual música do álbum Blurryface?', 'Ride', 'Doubt', 'Polarize', 'Goner', 'c'),
('final', 'Qual é o nome do projeto de música produzido por Tyler Joseph previamente à sua carreira no Twenty One Pilots?', 'No Phun Intended', 'Gray Car Riding', 'Effort Through The Desert', 'Kitchen Sink', 'a'),
('final', 'Em qual website as cartas de Clancy em relação à narrativa criada pela banda podem ser acessadas?', 'Em “bishops.dema”', 'Em “dema-clancy.info”', 'Em “demainformation.org”', 'Em “dmaorg.info”', 'd'),
('final', 'Em qual destes eventos a banda performou um cover da música Seven Nation Army?', 'Billboard Music Awards', 'Rock & Roll Hall of Fame', 'MTV Video Music Awards', 'Songwriters Hall of Fame', 'b'),
('final', 'Qual é a explicação dada por Tyler Joseph em relação ao logo da banda?', 'Um encorajamento para criar algo com significado próprio', 'Uma homenagem para a cidade onde a banda foi formada', 'Uma representação dos gêneros musicais explorados pela banda', 'Uma simbologia para os instrumentos tocados pelos integrantes', 'a'),
('final', 'No show realizado em 17 de outubro de 2026, no estádio de Ohio, qual foi a música tocada na abertura?', 'Car Radio', 'City Walls', 'Overcompensate', 'Goner', 'd'),
('final', 'De acordo com a narrativa explorada pela banda, qual destes elementos não está presente na cidade de Dema?', 'As nove torres', 'Lápides de néon', 'A grande cachoeira', 'Os nove distritos', 'c'),
('final', 'Quais são as cores nas roupas das crianças na capa do álbum Regional At Best?', 'Vermelho e amarelo', 'Roxo e verde', 'Azul e vermelho', 'Verde e Azul', 'c');