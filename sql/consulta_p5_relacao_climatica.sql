-- Pergunta 5 do canvas: "Existe relação entre as ocorrências de interrupção e
-- determinadas condições climáticas? Quais períodos e regiões apresentam
-- maior recorrência de interrupções associadas a condições climáticas?"
--
-- Filtro definitivo (corrigido em 24/09): usar grupo_causa = "Meio Ambiente"
-- pega categorias que NÃO são condição climática (queimada/incêndio,
-- corrosão, animais, erosão) -- a maior delas, "queimada ou incêndio", é
-- disparada a mais comum e teria distorcido toda a análise. O filtro certo
-- é direto no detalhe_causa, só nas 4 categorias realmente climáticas:
-- vento, descarga atmosférica (raio), inundação e árvore/vegetação (queda
-- por vento/tempestade). A palavra-chave usa "VEGETA" em vez de "ARVORE"
-- porque a versão acentuada ("Árvore") não seria pega por um ILIKE que
-- procura "ARVORE" sem acento -- "VEGETA" não tem acento em nenhuma das
-- duas grafias do banco (vegetação / VEGETACAO), então pega as duas.

-- =====================================================================
-- PASSO 1: região (município) x período (mês) com mais ocorrências de
-- causa climática, cruzado com o clima do dia (estação mais próxima,
-- até 50 km, priorizando a que tiver medição naquele dia -- se a mais
-- próxima não tiver, usa a 2ª ou 3ª).
-- =====================================================================
WITH ocorrencias_clima AS (
    SELECT
        o.id_ocorrencia,
        o.id_municipio,
        extract(year FROM o.inicio_ocorrencia)::smallint AS ano,
        date(o.inicio_ocorrencia) AS data_ocorrencia
    FROM dados.ocorrencia o
    JOIN dados.causa c ON c.id_causa = o.id_causa
    WHERE c.detalhe_causa ILIKE ANY (ARRAY['%VENTO%', '%DESCARGA ATMOSF%', '%INUNDA%', '%VEGETA%'])
      AND o.id_municipio <> '0000000'
      AND o.inicio_ocorrencia IS NOT NULL
)
SELECT
    m.nome_municipio,
    date_trunc('month', oc.data_ocorrencia)::date AS mes,
    COUNT(*) AS qtd_ocorrencias_clima,
    ROUND(AVG(cd.precipitacao_total_mm), 1) AS precipitacao_media_mm,
    ROUND(AVG(cd.rajada_max_ms), 1) AS rajada_media_ms
FROM ocorrencias_clima oc
JOIN dados.municipio m ON m.id_municipio = oc.id_municipio
JOIN LATERAL (
    SELECT cd.*
    FROM dados.municipio_estacao me
    JOIN dados.clima_diario cd
      ON cd.id_estacao = me.id_estacao AND cd.data_local = oc.data_ocorrencia
    WHERE me.id_municipio = oc.id_municipio
      AND me.ano = oc.ano
      AND me.distancia_km <= 50
    ORDER BY me.ordem
    LIMIT 1
) cd ON true
GROUP BY m.nome_municipio, mes
ORDER BY qtd_ocorrencias_clima DESC
LIMIT 30;

-- =====================================================================
-- PASSO 2: evidência de que existe relação -- clima médio nos dias com
-- ocorrência de causa climática vs. média geral de todos os dias medidos.
-- =====================================================================
WITH ocorrencias_clima AS (
    SELECT
        o.id_municipio,
        extract(year FROM o.inicio_ocorrencia)::smallint AS ano,
        date(o.inicio_ocorrencia) AS data_ocorrencia
    FROM dados.ocorrencia o
    JOIN dados.causa c ON c.id_causa = o.id_causa
    WHERE c.detalhe_causa ILIKE ANY (ARRAY['%VENTO%', '%DESCARGA ATMOSF%', '%INUNDA%', '%VEGETA%'])
      AND o.id_municipio <> '0000000'
      AND o.inicio_ocorrencia IS NOT NULL
),
clima_nos_dias_de_ocorrencia AS (
    SELECT cd.precipitacao_total_mm, cd.rajada_max_ms
    FROM ocorrencias_clima oc
    JOIN LATERAL (
        SELECT cd.*
        FROM dados.municipio_estacao me
        JOIN dados.clima_diario cd
          ON cd.id_estacao = me.id_estacao AND cd.data_local = oc.data_ocorrencia
        WHERE me.id_municipio = oc.id_municipio
          AND me.ano = oc.ano
          AND me.distancia_km <= 50
        ORDER BY me.ordem
        LIMIT 1
    ) cd ON true
)
SELECT 'Dias com ocorrência climática' AS grupo,
       ROUND(AVG(precipitacao_total_mm), 1) AS precipitacao_media_mm,
       ROUND(AVG(rajada_max_ms), 1) AS rajada_media_ms,
       COUNT(*) AS qtd_dias
FROM clima_nos_dias_de_ocorrencia
UNION ALL
SELECT 'Média geral (todos os dias com medição)',
       ROUND(AVG(precipitacao_total_mm), 1),
       ROUND(AVG(rajada_max_ms), 1),
       COUNT(*)
FROM dados.clima_diario;

-- =====================================================================
-- PASSO 3: sazonalidade por mês do ano (todos os anos somados).
-- =====================================================================
SELECT
    extract(month FROM o.inicio_ocorrencia)::int AS mes_do_ano,
    COUNT(*) AS qtd_ocorrencias_clima
FROM dados.ocorrencia o
JOIN dados.causa c ON c.id_causa = o.id_causa
WHERE c.detalhe_causa ILIKE ANY (ARRAY['%VENTO%', '%DESCARGA ATMOSF%', '%INUNDA%', '%VEGETA%'])
  AND o.id_municipio <> '0000000'
GROUP BY mes_do_ano
ORDER BY mes_do_ano;
