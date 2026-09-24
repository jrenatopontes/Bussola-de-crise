-- Pergunta 2 do canvas: "Quando elas acontecem: existe alguma sazonalidade
-- ao longo dos meses ou uma concentração em horários específicos do dia?"

-- 0) Confiabilidade da base: quantas interrupções não têm data de início.
-- Antes de confiar nos rankings abaixo, mede o quanto da base fica de fora
-- por falta de data (ex.: linhas do schema novo de 2026, ver achado #5a).
SELECT
    COUNT(*) FILTER (WHERE inicio_interrupcao IS NULL) AS sem_data_inicio,
    COUNT(*) AS total_interrupcoes
FROM dados.interrupcao;

-- 1) Sazonalidade por MÊS.
-- Soma todas as interrupções de 2021 a 2025 por mês do ano (independente
-- do ano). Orienta planejamento de sobreaviso e contratação temporária em
-- meses críticos (ex.: época de chuva), e manutenção preventiva nos meses
-- de menor volume.
SELECT
    EXTRACT(MONTH FROM inicio_interrupcao) AS mes,
    COUNT(*) AS qtd_interrupcoes
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
GROUP BY mes
ORDER BY mes;

-- 2) Sazonalidade por HORÁRIO DO DIA.
-- Mesma lógica, mas por hora de início (0 a 23h). Orienta o dimensionamento
-- de turnos e escala das equipes de campo ao longo do dia.
SELECT
    EXTRACT(HOUR FROM inicio_interrupcao) AS hora,
    COUNT(*) AS qtd_interrupcoes
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
GROUP BY hora
ORDER BY hora;

-- 3) Sazonalidade por mês, ano a ano.
-- Quebra o resultado da consulta 1 por ano, para verificar se o padrão de
-- sazonalidade se repete todo ano ou se é influenciado por algum ano
-- atípico (o que mudaria a confiança na recomendação de contratação
-- temporária/sobreaviso).
SELECT
    EXTRACT(YEAR FROM inicio_interrupcao) AS ano,
    EXTRACT(MONTH FROM inicio_interrupcao) AS mes,
    COUNT(*) AS qtd_interrupcoes
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
GROUP BY ano, mes
ORDER BY ano, mes;

-- 4) Cruzamento com consumidores afetados, por mês.
-- Mostra não só quantas interrupções, mas o impacto real em consumidores
-- por mês -- diferencia "mês com muitas interrupções pequenas" de "mês com
-- poucas interrupções que afetam muita gente", o que pesa mais na decisão
-- de reforçar equipe em determinado período.
SELECT
    EXTRACT(MONTH FROM inicio_interrupcao) AS mes,
    COUNT(*) AS qtd_interrupcoes,
    SUM(consumidores_afetados) AS total_consumidores_afetados
FROM dados.interrupcao
WHERE inicio_interrupcao IS NOT NULL
GROUP BY mes
ORDER BY mes;
