-- Pergunta 3 do canvas: "Por que elas acontecem: quais são as causas mais
-- frequentes e quais delas demandam mais tempo para solução?"
-- ATENÇÃO, UTILIZEI UM FILTRO PARA RETIRAR OS DADOS DE 2026 DA CONSULTA.

-- ============================================================
-- PONTO 0 — VALIDAÇÃO DOS DADOS
-- Verifica se existem dados faltantes nos campos utilizados
-- na análise de duração das ocorrências (2021 a 2025).
-- ============================================================

SELECT
    COUNT(*) AS total_ocorrencias,
    COUNT(*) FILTER (WHERE tempo_preparacao IS NULL) AS sem_tempo_preparacao,
    COUNT(*) FILTER (WHERE tempo_deslocamento IS NULL) AS sem_tempo_deslocamento,
    COUNT(*) FILTER (WHERE tempo_execucao IS NULL) AS sem_tempo_execucao,
    COUNT(*) FILTER (
        WHERE inicio_ocorrencia IS NULL
           OR fim_ocorrencia IS NULL
    ) AS sem_data_inicio_ou_fim
FROM dados.ocorrencia
WHERE inicio_ocorrencia < '2026-01-01';


-- ============================================================
-- PONTO 1 — FREQUÊNCIA POR GRUPO DE CAUSA
-- Identifica quais grupos de causa concentram o maior número
-- de ocorrências e qual a participação percentual de cada um.
-- ============================================================

SELECT
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    COUNT(*) AS qtd_ocorrencias,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentual
FROM dados.ocorrencia o
JOIN dados.causa c
    ON c.id_causa = o.id_causa
WHERE o.inicio_ocorrencia < '2026-01-01'
GROUP BY UPPER(TRIM(c.grupo_causa))
ORDER BY qtd_ocorrencias DESC;


-- ============================================================
-- PONTO 2 — FREQUÊNCIA POR CAUSA ESPECÍFICA
-- Detalha os grupos de causa para identificar as causas
-- específicas mais frequentes no período analisado.
-- ============================================================

SELECT
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    UPPER(TRIM(c.detalhe_causa)) AS detalhe_causa,
    COUNT(*) AS qtd_ocorrencias,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentual
FROM dados.ocorrencia o
JOIN dados.causa c
    ON c.id_causa = o.id_causa
WHERE o.inicio_ocorrencia < '2026-01-01'
  AND c.detalhe_causa IS NOT NULL
GROUP BY
    UPPER(TRIM(c.grupo_causa)),
    UPPER(TRIM(c.detalhe_causa))
ORDER BY qtd_ocorrencias DESC
LIMIT 20;


-- ============================================================
-- PONTO 3 — DURAÇÃO POR GRUPO DE CAUSA
-- Compara o tempo de solução entre os grupos de causa,
-- considerando preparação, deslocamento e execução.
-- A mediana representa a duração típica das ocorrências.
-- ============================================================

SELECT
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    COUNT(*) AS qtd_ocorrencias,

    ROUND(AVG(
        o.tempo_preparacao
        + o.tempo_deslocamento
        + o.tempo_execucao
    ), 1) AS duracao_media_min,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY
            o.tempo_preparacao
            + o.tempo_deslocamento
            + o.tempo_execucao
    )::numeric, 1) AS duracao_mediana_min,

    ROUND(AVG(o.tempo_preparacao), 1) AS media_preparo_min,
    ROUND(AVG(o.tempo_deslocamento), 1) AS media_deslocamento_min,
    ROUND(AVG(o.tempo_execucao), 1) AS media_execucao_min

FROM dados.ocorrencia o
JOIN dados.causa c
    ON c.id_causa = o.id_causa

WHERE o.inicio_ocorrencia < '2026-01-01'
  AND o.tempo_preparacao IS NOT NULL
  AND o.tempo_deslocamento IS NOT NULL
  AND o.tempo_execucao IS NOT NULL

GROUP BY UPPER(TRIM(c.grupo_causa))
ORDER BY duracao_mediana_min DESC;


-- ============================================================
-- PONTO 4 — FREQUÊNCIA X DURAÇÃO POR CAUSA
-- Cruza a quantidade de ocorrências com a duração mediana
-- para identificar causas frequentes e/ou de maior duração.
-- ============================================================

SELECT
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    UPPER(TRIM(c.detalhe_causa)) AS detalhe_causa,
    COUNT(*) AS qtd_ocorrencias,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY
            o.tempo_preparacao
            + o.tempo_deslocamento
            + o.tempo_execucao
    )::numeric, 1) AS duracao_mediana_min

FROM dados.ocorrencia o
JOIN dados.causa c
    ON c.id_causa = o.id_causa

WHERE o.inicio_ocorrencia < '2026-01-01'
  AND o.tempo_preparacao IS NOT NULL
  AND o.tempo_deslocamento IS NOT NULL
  AND o.tempo_execucao IS NOT NULL
  AND c.detalhe_causa IS NOT NULL

GROUP BY
    UPPER(TRIM(c.grupo_causa)),
    UPPER(TRIM(c.detalhe_causa))

HAVING COUNT(*) >= 30

ORDER BY qtd_ocorrencias DESC, duracao_mediana_min DESC
LIMIT 20;


-- ============================================================
-- PONTO 5 — DECOMPOSIÇÃO DO TEMPO POR CAUSA
-- Identifica as causas com maior duração mediana e compara
-- os tempos médios de preparação, deslocamento e execução.
-- ============================================================

SELECT
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    UPPER(TRIM(c.detalhe_causa)) AS detalhe_causa,
    COUNT(*) AS qtd_ocorrencias,

    ROUND(AVG(o.tempo_preparacao), 1) AS media_preparo_min,
    ROUND(AVG(o.tempo_deslocamento), 1) AS media_deslocamento_min,
    ROUND(AVG(o.tempo_execucao), 1) AS media_execucao_min,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY
            o.tempo_preparacao
            + o.tempo_deslocamento
            + o.tempo_execucao
    )::numeric, 1) AS duracao_mediana_total_min

FROM dados.ocorrencia o
JOIN dados.causa c
    ON c.id_causa = o.id_causa

WHERE o.inicio_ocorrencia < '2026-01-01'
  AND o.tempo_preparacao IS NOT NULL
  AND o.tempo_deslocamento IS NOT NULL
  AND o.tempo_execucao IS NOT NULL
  AND c.detalhe_causa IS NOT NULL

GROUP BY
    UPPER(TRIM(c.grupo_causa)),
    UPPER(TRIM(c.detalhe_causa))

HAVING COUNT(*) >= 30

ORDER BY duracao_mediana_total_min DESC;


-- ============================================================
-- PONTO 6 — MÉDIA, MEDIANA, P75 E P90
-- Analisa a distribuição da duração para diferenciar causas
-- normalmente demoradas de ocorrências excepcionalmente longas.
-- ============================================================

SELECT
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    UPPER(TRIM(c.detalhe_causa)) AS detalhe_causa,
    COUNT(*) AS qtd_ocorrencias,

    ROUND(AVG(
        o.tempo_preparacao
        + o.tempo_deslocamento
        + o.tempo_execucao
    ), 1) AS media_total_min,

    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (
        ORDER BY
            o.tempo_preparacao
            + o.tempo_deslocamento
            + o.tempo_execucao
    )::numeric, 1) AS mediana_min,

    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (
        ORDER BY
            o.tempo_preparacao
            + o.tempo_deslocamento
            + o.tempo_execucao
    )::numeric, 1) AS p75_min,

    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (
        ORDER BY
            o.tempo_preparacao
            + o.tempo_deslocamento
            + o.tempo_execucao
    )::numeric, 1) AS p90_min

FROM dados.ocorrencia o
JOIN dados.causa c
    ON c.id_causa = o.id_causa

WHERE o.inicio_ocorrencia < '2026-01-01'
  AND o.tempo_preparacao IS NOT NULL
  AND o.tempo_deslocamento IS NOT NULL
  AND o.tempo_execucao IS NOT NULL
  AND c.detalhe_causa IS NOT NULL

GROUP BY
    UPPER(TRIM(c.grupo_causa)),
    UPPER(TRIM(c.detalhe_causa))

HAVING COUNT(*) >= 30

ORDER BY mediana_min DESC;