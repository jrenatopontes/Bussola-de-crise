-- Pergunta 2 do canvas: "Quando elas acontecem: existe alguma sazonalidade
-- ao longo dos meses ou uma concentração em horários específicos do dia?"
--
-- NOTA METODOLÓGICA: 2026 é excluído em toda consulta que soma/agrupa por
-- mês, causa ou clima, porque o ano só tem dados até 30/06 -- misturar com
-- os 5 anos completos infla artificialmente jan-jun frente a jul-dez.
-- A única exceção é a consulta 2 (sazonalidade por horário), que não sofre
-- esse viés (todo dia tem 24h, completo ou não).

-- 0) Confiabilidade da base: quantas interrupções não têm data de início.
SELECT
    COUNT(*) FILTER (WHERE inicio_interrupcao IS NULL) AS sem_data_inicio,
    COUNT(*) AS total_interrupcoes
FROM dados.interrupcao;

-- 1) Sazonalidade por MÊS -- só 2021-2025 (anos completos).
SELECT
    EXTRACT(MONTH FROM inicio_interrupcao) AS mes,
    COUNT(*) AS qtd_interrupcoes
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
  AND EXTRACT(YEAR FROM inicio_interrupcao) BETWEEN 2021 AND 2025
GROUP BY mes
ORDER BY mes;

-- 2) Sazonalidade por HORÁRIO DO DIA -- todos os anos (sem viés de ano parcial).
SELECT
    EXTRACT(HOUR FROM inicio_interrupcao) AS hora,
    COUNT(*) AS qtd_interrupcoes
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
GROUP BY hora
ORDER BY hora;

-- 3) Sazonalidade por mês, ano a ano -- inclui 2026 separado (não soma com o resto).
SELECT
    EXTRACT(YEAR FROM inicio_interrupcao) AS ano,
    EXTRACT(MONTH FROM inicio_interrupcao) AS mes,
    COUNT(*) AS qtd_interrupcoes
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
GROUP BY ano, mes
ORDER BY ano, mes;

-- 4) Cruzamento com consumidores afetados, por mês -- só 2021-2025.
SELECT
    EXTRACT(MONTH FROM inicio_interrupcao) AS mes,
    COUNT(*) AS qtd_interrupcoes,
    SUM(consumidores_afetados) AS total_consumidores_afetados
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
  AND EXTRACT(YEAR FROM inicio_interrupcao) BETWEEN 2021 AND 2025
GROUP BY mes
ORDER BY mes;

-- =====================================================================
-- INVESTIGAÇÃO: por que outubro tem o maior impacto médio por evento?
-- (volume moderado, mas maior consumidores_afetados/interrupção do ano)
-- =====================================================================

-- 5) Clima médio por mês (temperatura e chuva) -- só 2021-2025.
-- Testa a hipótese de chuva/calor como explicação.
SELECT
    EXTRACT(MONTH FROM data_local) AS mes,
    ROUND(AVG(temp_max_c), 1) AS temp_max_media,
    ROUND(AVG(temp_min_c), 1) AS temp_min_media,
    ROUND(AVG(precipitacao_total_mm), 1) AS chuva_media_mm_dia,
    COUNT(*) FILTER (WHERE precipitacao_total_mm IS NOT NULL) AS dias_com_medicao_chuva,
    COUNT(*) AS total_dias_estacao
FROM dados.clima_diario
WHERE EXTRACT(YEAR FROM data_local) BETWEEN 2021 AND 2025
GROUP BY mes
ORDER BY mes;

-- 6) Rajada de vento média e máxima por mês -- só 2021-2025.
-- Testa a hipótese de vento como explicação.
SELECT
    EXTRACT(MONTH FROM data_local) AS mes,
    ROUND(AVG(rajada_max_ms), 1) AS rajada_media_ms,
    ROUND(MAX(rajada_max_ms), 1) AS rajada_maxima_ms
FROM dados.clima_diario
WHERE EXTRACT(YEAR FROM data_local) BETWEEN 2021 AND 2025
GROUP BY mes
ORDER BY mes;

-- 7) Causas mais frequentes em OUTUBRO -- só 2021-2025.
SELECT
    c.grupo_causa,
    COUNT(*) AS qtd_em_outubro
FROM dados.interrupcao i
JOIN dados.ocorrencia o ON o.id_ocorrencia = i.id_ocorrencia
JOIN dados.causa c ON c.id_causa = o.id_causa
WHERE EXTRACT(MONTH FROM i.inicio_interrupcao) = 10
  AND EXTRACT(YEAR FROM i.inicio_interrupcao) BETWEEN 2021 AND 2025
GROUP BY c.grupo_causa
ORDER BY qtd_em_outubro DESC;

-- 8) Causas mais frequentes em MARÇO (comparação -- mês de maior volume) -- só 2021-2025.
SELECT
    c.grupo_causa,
    COUNT(*) AS qtd_em_marco
FROM dados.interrupcao i
JOIN dados.ocorrencia o ON o.id_ocorrencia = i.id_ocorrencia
JOIN dados.causa c ON c.id_causa = o.id_causa
WHERE EXTRACT(MONTH FROM i.inicio_interrupcao) = 3
  AND EXTRACT(YEAR FROM i.inicio_interrupcao) BETWEEN 2021 AND 2025
GROUP BY c.grupo_causa
ORDER BY qtd_em_marco DESC;

-- 9) Impacto médio por consumidor, por tipo de causa (geral, todos os meses) -- só 2021-2025.
-- Testa se o tipo de causa por si só explica diferenças de impacto médio.
SELECT
    c.grupo_causa,
    COUNT(*) AS qtd_interrupcoes,
    ROUND(AVG(i.consumidores_afetados), 1) AS media_consumidores_por_evento
FROM dados.interrupcao i
JOIN dados.ocorrencia o ON o.id_ocorrencia = i.id_ocorrencia
JOIN dados.causa c ON c.id_causa = o.id_causa
WHERE EXTRACT(YEAR FROM i.inicio_interrupcao) BETWEEN 2021 AND 2025
GROUP BY c.grupo_causa
ORDER BY media_consumidores_por_evento DESC;

-- 10) Os 20 maiores eventos individuais de outubro (por consumidores afetados) -- só 2021-2025.
-- Testa se o impacto médio maior é puxado por poucos eventos extremos
-- concentrados, ou é um padrão distribuído/recorrente.
SELECT
    i.id_interrupcao,
    i.consumidores_afetados,
    c.grupo_causa,
    EXTRACT(YEAR FROM i.inicio_interrupcao) AS ano
FROM dados.interrupcao i
JOIN dados.ocorrencia o ON o.id_ocorrencia = i.id_ocorrencia
JOIN dados.causa c ON c.id_causa = o.id_causa
WHERE EXTRACT(MONTH FROM i.inicio_interrupcao) = 10
  AND EXTRACT(YEAR FROM i.inicio_interrupcao) BETWEEN 2021 AND 2025
ORDER BY i.consumidores_afetados DESC
LIMIT 20;
