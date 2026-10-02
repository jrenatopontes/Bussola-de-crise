/* ====================================================================================
   PERGUNTA 2: SAZONALIDADE (MÊS E HORÁRIO)
   Objetivo: Identificar padrões temporais (quando a rede mais falha) para 
             otimização de escalas de equipes de plantão.
             
   Lógica aplicada no Dashboard (Looker Studio):
   1. Base Flat: A query foi simplificada para exportar dados granulares, 
      deixando as agregações (SUM, COUNT) para o Looker Studio.
   2. Gráfico de Colunas (Mês): Aplicado filtro visual para excluir o ano de 2026 
      (incompleto), evitando distorções no primeiro semestre. Criado campo calculado 
      com CASE WHEN para converter o número do mês em texto (Jan, Fev, etc.).
   3. Gráfico de Linhas (Hora): O ano de 2026 foi mantido, pois meses incompletos 
      não distorcem a proporção das 24 horas do dia. Criado campo calculado com 
      CONCAT() para adicionar a letra "h" e a ordenação foi ajustada pela agregação
      MÍNIMA da hora para evitar que a ferramenta somasse os eixos.
==================================================================================== */

SELECT 
    i.id_interrupcao,
    EXTRACT(YEAR FROM i.inicio_interrupcao) AS ano,
    EXTRACT(MONTH FROM i.inicio_interrupcao) AS mes,
    EXTRACT(HOUR FROM i.inicio_interrupcao) AS hora,
    i.consumidores_afetados,
    c.grupo_causa
FROM 
    dados.interrupcao i
JOIN 
    dados.ocorrencia o ON o.id_ocorrencia = i.id_ocorrencia
JOIN 
    dados.causa c ON c.id_causa = o.id_causa
WHERE 
    i.inicio_interrupcao IS NOT NULL;