
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




