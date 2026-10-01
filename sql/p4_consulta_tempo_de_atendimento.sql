
-- Pergunta 4: qual a duração de cada etapa (preparo, deslocamento, execução) e onde esse tempo é pior?
-- Base: dados.ocorrencia (ANEEL, Celpe). Tempos em minutos.
-- Atenção: dados.ocorrencia só tem as ocorrências ligadas a pelo menos uma interrupção.


-- colunas existentes
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'dados' AND table_name = 'ocorrencia'
ORDER BY ordinal_position;

-- primeiras linhas
SELECT * FROM dados.ocorrencia LIMIT 10;

-- total de linhas e linhas com tempo (a diferença são as substitutas, sem tempo)
SELECT COUNT(*) AS linhas,
       COUNT(tempo_preparacao) AS com_tempo
FROM dados.ocorrencia;

-- conferência da duração total de cada atendimento: soma das três etapas

SELECT o.num_ocorrencia_origem,
       m.nome_municipio,
       o.tempo_preparacao,
       o.tempo_deslocamento,
       o.tempo_execucao,
       o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao AS duracao_total_min
FROM dados.ocorrencia o
JOIN dados.municipio m ON m.id_municipio = o.id_municipio
WHERE o.tempo_preparacao IS NOT NULL
LIMIT 20;

-- média e mediana de cada etapa em PE
SELECT ROUND(AVG(tempo_preparacao), 1) AS media_preparo_min,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY tempo_preparacao)::numeric, 1) AS mediana_preparo_min,
       ROUND(AVG(tempo_deslocamento), 1) AS media_deslocamento_min,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY tempo_deslocamento)::numeric, 1) AS mediana_deslocamento_min,
       ROUND(AVG(tempo_execucao), 1) AS media_execucao_min,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY tempo_execucao)::numeric, 1) AS mediana_execucao_min
FROM dados.ocorrencia;

-- mediana da duração total por município, sem o "Não identificado"
SELECT m.nome_municipio,
       COUNT(*) AS total_ocorrencias,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao)::numeric, 1) AS mediana_total_min
FROM dados.ocorrencia o
JOIN dados.municipio m ON m.id_municipio = o.id_municipio
WHERE o.id_municipio <> '0000000'
GROUP BY m.id_municipio, m.nome_municipio
ORDER BY mediana_total_min DESC;

-- mediana da duração total por conjunto elétrico
-- as substitutas têm conjunto mas não têm tempo: saem no WHERE para não entrar no COUNT
SELECT c.nome_conjunto,
       COUNT(*) AS total_ocorrencias,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao)::numeric, 1) AS mediana_total_min
FROM dados.ocorrencia o
JOIN dados.conjunto_eletrico c ON c.id_conjunto = o.id_conjunto
WHERE o.tempo_preparacao IS NOT NULL
GROUP BY c.id_conjunto, c.nome_conjunto
HAVING COUNT(*) >= 30
ORDER BY mediana_total_min DESC;

-- ocorrências por município, sem o "Não identificado"
SELECT m.nome_municipio,
       COUNT(*) AS total
FROM dados.ocorrencia o
JOIN dados.municipio m ON m.id_municipio = o.id_municipio
WHERE o.id_municipio <> '0000000'
GROUP BY m.id_municipio, m.nome_municipio
ORDER BY total DESC;

-- onde a rede quebra mais e o conserto demora mais: ranking dos conjuntos elétricos
-- frequência = ocorrências por mil consumidores (compara conjuntos de tamanhos diferentes)
-- demora = mediana da duração total do atendimento
-- só conjuntos com 30 ou mais ocorrências
SELECT c.nome_conjunto,
       c.total_consumidores,
       COUNT(*) AS ocorrencias,
       ROUND(1000.0 * COUNT(*) / c.total_consumidores, 1) AS ocorrencias_por_mil_consumidores,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao)::numeric, 1) AS mediana_total_min
FROM dados.ocorrencia o
JOIN dados.conjunto_eletrico c ON c.id_conjunto = o.id_conjunto
WHERE o.id_municipio <> '0000000'
GROUP BY c.id_conjunto, c.nome_conjunto, c.total_consumidores
HAVING COUNT(*) >= 30
ORDER BY ocorrencias_por_mil_consumidores DESC;



-- PARTE 2: consultas usadas na análise (analise_p4_tempo_atendimento.md)
--
-- Todas começam com um WITH que monta uma tabela temporária "base",
-- com a duração total já calculada (soma das três etapas). Assim a
-- conta não precisa ser repetida em cada coluna do SELECT.
-- percentile_cont(0.5) é a mediana. O ::numeric é necessário porque
-- percentile_cont devolve double precision e o ROUND(x, 1) do
-- PostgreSQL só aceita numeric (sem ele dá o erro 42883).


-- ---------------------------------------------------------------------
-- 2.1  Pernambuco inteiro: média, mediana e parcela de cada etapa
--      (seção 2 do md)
-- Filtro: tempo_preparacao IS NOT NULL pega todas as ocorrências
-- reais, inclusive as poucas com código IBGE fora de PE.
-- pct_*: quanto do tempo total gasto (somando todos os atendimentos)
-- ficou em cada etapa.
-- Resultado (30/09/2026): 852.674 ocorrências; medianas 125,1 / 33,5 /
-- 46,9 / total 274,0 min; parcelas 50,2% / 6,5% / 43,3%.
-- ---------------------------------------------------------------------
WITH base AS (
    SELECT tempo_preparacao   AS preparo,
           tempo_deslocamento AS deslocamento,
           tempo_execucao     AS execucao,
           tempo_preparacao + tempo_deslocamento + tempo_execucao AS total
    FROM dados.ocorrencia
    WHERE tempo_preparacao IS NOT NULL
)
SELECT COUNT(*) AS ocorrencias,
       ROUND(AVG(preparo), 1) AS media_preparo,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY preparo)::numeric, 1) AS mediana_preparo,
       ROUND(AVG(deslocamento), 1) AS media_desloc,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY deslocamento)::numeric, 1) AS mediana_desloc,
       ROUND(AVG(execucao), 1) AS media_exec,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY execucao)::numeric, 1) AS mediana_exec,
       ROUND(AVG(total), 1) AS media_total,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY total)::numeric, 1) AS mediana_total,
       ROUND(100 * SUM(preparo) / SUM(total), 1) AS pct_preparo,
       ROUND(100 * SUM(deslocamento) / SUM(total), 1) AS pct_desloc,
       ROUND(100 * SUM(execucao) / SUM(total), 1) AS pct_exec
FROM base;

-- ---------------------------------------------------------------------
-- 2.2  Por ano: o padrão se repete? (seção 3 do md)
-- O ano vem dos 4 últimos caracteres de num_ocorrencia_origem, que tem
-- o formato "{número da ocorrência}_{ano do arquivo}".
-- Conferência: a linha de 2025 bateu com a consulta feita quando o
-- banco tinha só 2025 (preparo 134,0 / total 270,7).
-- ---------------------------------------------------------------------
WITH base AS (
    SELECT RIGHT(num_ocorrencia_origem, 4) AS ano,
           tempo_preparacao   AS preparo,
           tempo_deslocamento AS deslocamento,
           tempo_execucao     AS execucao,
           tempo_preparacao + tempo_deslocamento + tempo_execucao AS total
    FROM dados.ocorrencia
    WHERE tempo_preparacao IS NOT NULL
)
SELECT ano,
       COUNT(*) AS ocorrencias,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY preparo)::numeric, 1) AS mediana_preparo,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY deslocamento)::numeric, 1) AS mediana_desloc,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY execucao)::numeric, 1) AS mediana_exec,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY total)::numeric, 1) AS mediana_total,
       ROUND(AVG(total), 1) AS media_total
FROM base
GROUP BY ano
ORDER BY ano;

-- ---------------------------------------------------------------------
-- 2.3  Os 20 municípios com maior mediana de duração total
--      (seção 4 do md)
-- Filtro: id_municipio <> '0000000' tira o "Não identificado" (as
-- substitutas e as ocorrências com código IBGE fora de PE).
-- HAVING COUNT(*) >= 30: mínimo de ocorrências para a mediana fazer
-- sentido. No período 2021-2025 nenhum município do top 20 chega perto
-- desse limite (o menor tem 962).
-- ---------------------------------------------------------------------
WITH base AS (
    SELECT o.id_municipio,
           o.tempo_preparacao   AS preparo,
           o.tempo_deslocamento AS deslocamento,
           o.tempo_execucao     AS execucao,
           o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao AS total
    FROM dados.ocorrencia o
    WHERE o.id_municipio <> '0000000'
)
SELECT m.nome_municipio,
       COUNT(*) AS ocorrencias,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.preparo)::numeric, 1) AS mediana_preparo,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.deslocamento)::numeric, 1) AS mediana_desloc,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.execucao)::numeric, 1) AS mediana_exec,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.total)::numeric, 1) AS mediana_total,
       ROUND(AVG(b.total), 1) AS media_total
FROM base b
JOIN dados.municipio m ON m.id_municipio = b.id_municipio
GROUP BY m.id_municipio, m.nome_municipio
HAVING COUNT(*) >= 30
ORDER BY mediana_total DESC
LIMIT 20;

-- ---------------------------------------------------------------------
-- 2.4  Os 20 conjuntos elétricos com maior mediana de duração total
--      (seção 5 do md)
-- Filtro: tempo_preparacao IS NOT NULL (as ocorrências reais têm
-- conjunto válido mesmo quando o município é "Não identificado").
-- Atenção: o conjunto de cada ocorrência vem da primeira interrupção
-- ligada a ela; ver limitações no md.
-- ---------------------------------------------------------------------
WITH base AS (
    SELECT o.id_conjunto,
           o.tempo_preparacao   AS preparo,
           o.tempo_deslocamento AS deslocamento,
           o.tempo_execucao     AS execucao,
           o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao AS total
    FROM dados.ocorrencia o
    WHERE o.tempo_preparacao IS NOT NULL
)
SELECT c.id_conjunto,
       c.nome_conjunto,
       COUNT(*) AS ocorrencias,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.preparo)::numeric, 1) AS mediana_preparo,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.deslocamento)::numeric, 1) AS mediana_desloc,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.execucao)::numeric, 1) AS mediana_exec,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY b.total)::numeric, 1) AS mediana_total,
       ROUND(AVG(b.total), 1) AS media_total
FROM base b
JOIN dados.conjunto_eletrico c ON c.id_conjunto = b.id_conjunto
GROUP BY c.id_conjunto, c.nome_conjunto
HAVING COUNT(*) >= 30
ORDER BY mediana_total DESC
LIMIT 20;


-- =====================================================================
-- PARTE 3: consultas extras (não usadas no md)
-- =====================================================================

-- ocorrências por município, sem o "Não identificado"
SELECT m.nome_municipio,
       COUNT(*) AS total
FROM dados.ocorrencia o
JOIN dados.municipio m ON m.id_municipio = o.id_municipio
WHERE o.id_municipio <> '0000000'
GROUP BY m.id_municipio, m.nome_municipio
ORDER BY total DESC;

-- onde a rede quebra mais e o conserto demora mais: ranking dos conjuntos elétricos
-- frequência = ocorrências por mil consumidores (compara conjuntos de tamanhos diferentes)
-- demora = mediana da duração total do atendimento
-- só conjuntos com 30 ou mais ocorrências
-- Atenção: total_consumidores é o valor da interrupção mais recente de cada
-- conjunto (foto atual), enquanto as ocorrências somam 2021 a 2025.
SELECT c.nome_conjunto,
       c.total_consumidores,
       COUNT(*) AS ocorrencias,
       ROUND(1000.0 * COUNT(*) / c.total_consumidores, 1) AS ocorrencias_por_mil_consumidores,
       ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao)::numeric, 1) AS mediana_total_min
FROM dados.ocorrencia o
JOIN dados.conjunto_eletrico c ON c.id_conjunto = o.id_conjunto
WHERE o.id_municipio <> '0000000'
GROUP BY c.id_conjunto, c.nome_conjunto, c.total_consumidores
HAVING COUNT(*) >= 30
ORDER BY ocorrencias_por_mil_consumidores DESC;
