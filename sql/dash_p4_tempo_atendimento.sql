/* ====================================================================================
   PERGUNTA 4: ETAPAS DE ATENDIMENTO E GARGALOS LOCAIS
   Objetivo: Detalhar o tempo gasto nas etapas (preparo, deslocamento, execução) 
             e mapear os municípios e conjuntos elétricos com a maior demora.
             
   Lógica aplicada no Dashboard (Looker Studio):
   1. Base Flat: Cruzamento das ocorrências com a geografia (município e conjunto).
      As agregações (médias das etapas) serão feitas dinamicamente no Looker.
   2. Tratamento de Qualidade: Filtro 'tempo_preparacao IS NOT NULL' para remover 
      ocorrências sem dados de tempo (substitutas) e município <> '0000000' para 
      excluir os "Não identificados".
   3. Pré-cálculo: A soma (tempo_total_min) foi adiantada no banco de dados.
   4. Recorte Temporal: Filtro < '2026-01-01' mantido para analisar anos fechados.
==================================================================================== */

SELECT 
    o.id_ocorrencia,
    EXTRACT(YEAR FROM o.inicio_ocorrencia) AS ano,
    m.nome_municipio,
    c.nome_conjunto,
    o.tempo_preparacao,
    o.tempo_deslocamento,
    o.tempo_execucao,
    (o.tempo_preparacao + o.tempo_deslocamento + o.tempo_execucao) AS tempo_total_min
FROM 
    dados.ocorrencia o
JOIN 
    dados.municipio m ON m.id_municipio = o.id_municipio
LEFT JOIN 
    dados.conjunto_eletrico c ON c.id_conjunto = o.id_conjunto
WHERE 
    o.tempo_preparacao IS NOT NULL
    AND o.id_municipio <> '0000000'
    AND o.inicio_ocorrencia < '2026-01-01';