/* ====================================================================================
   PERGUNTA 3: CAUSAS E TEMPO DE ATENDIMENTO
   Objetivo: Mapear os motivos mais frequentes de queda de energia e identificar 
             quais deles exigem o maior tempo de resposta das equipes.
             
   Lógica aplicada no Dashboard (Looker Studio):
   1. Base Flat: Extraímos os dados na menor granularidade (por id_ocorrencia).
      O agrupamento e as contagens serão feitos de forma dinâmica nos gráficos.
   2. Tratamento de Qualidade: O UPPER(TRIM()) foi mantido da análise original para 
      garantir que falhas de digitação (ex: " Árvore" vs "árvore") não quebrem o 
      agrupamento no painel.
   3. Cálculo de SLA: Somamos o preparo, deslocamento e execução numa nova coluna 
      (tempo_total_min) diretamente no banco, poupando processamento no BI.
   4. Regras de Negócio (Filtros): Conforme validação exploratória, o ano de 2026 
      foi removido via SQL ('2026-01-01') para evitar viés, e linhas sem medição de 
      tempo foram excluídas para não distorcer as médias do dashboard.
==================================================================================== */

SELECT 
    o.id_ocorrencia,
    UPPER(TRIM(c.grupo_causa)) AS grupo_causa,
    UPPER(TRIM(c.detalhe_causa)) AS detalhe_causa,
    o.tempo_preparacao,
    o.tempo_deslocamento,
    o.tempo_execucao,
    (o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao) AS tempo_total_min
FROM 
    dados.ocorrencia o
JOIN 
    dados.causa c ON c.id_causa = o.id_causa
WHERE 
    o.inicio_ocorrencia < '2026-01-01'
    AND o.tempo_preparacao IS NOT NULL
    AND o.tempo_deslocamento IS NOT NULL
    AND o.tempo_execucao IS NOT NULL;