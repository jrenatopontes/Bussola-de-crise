/* ====================================================================================
   PERGUNTA 1: CONCENTRAÇÃO GEOGRÁFICA
   Objetivo: Identificar as áreas com maior volume de ocorrências emergenciais 
             para orientar a alocação de equipes de plantão.
             
   Lógica aplicada no Dashboard (Looker Studio):
   1. Mapa de Bolhas: Focado no 'nome_municipio'. Foi feito um enriquecimento na 
      ferramenta de visualização concatenando ", Pernambuco, Brasil" para 
      garantir a precisão da geolocalização do Google Maps.
   2. Gráfico de Barras: Agrupado por 'nome_municipio' para manter coerência visual 
      com o mapa.
   3. Qualidade de Dados: O valor "Não identificado" foi removido via filtro na 
      visualização.
   4. O campo 'nome_conjunto' é extraído para manter a granularidade fina no CSV, 
      permitindo que o Looker Studio faça a agregação dinâmica.
==================================================================================== */

SELECT
    m.nome_municipio,
    c.nome_conjunto,
    COUNT(o.id_ocorrencia) as total_ocorrencias
FROM
    dados.ocorrencia o
JOIN
    dados.municipio m ON o.id_municipio = m.id_municipio
JOIN
    dados.conjunto_eletrico c ON o.id_conjunto = c.id_conjunto
GROUP BY
    m.nome_municipio,
    c.nome_conjunto
ORDER BY
    total_ocorrencias DESC;