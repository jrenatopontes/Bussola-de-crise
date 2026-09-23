-- Pergunta 1 do canvas: "Onde se concentram as ocorrências emergenciais em
-- Pernambuco: quais municípios e conjuntos elétricos registram o maior
-- volume?"

-- 1) Top 20 municípios por volume de ocorrências.
-- Mostra onde a Neoenergia deveria priorizar equipes de campo de forma
-- geral. Exclui o município sentinela "não identificado".
SELECT
    m.nome_municipio,
    COUNT(*) AS qtd_ocorrencias
FROM dados.ocorrencia o
JOIN dados.municipio m ON m.id_municipio = o.id_municipio
WHERE m.id_municipio <> '0000000'
GROUP BY m.nome_municipio
ORDER BY qtd_ocorrencias DESC
LIMIT 20;

-- 2) Top 20 conjuntos elétricos por volume de ocorrências.
-- Um conjunto elétrico é um recorte de rede menor que o município --
-- aponta com mais precisão qual trecho da rede precisa de investimento
-- em infraestrutura (poda, troca de equipamento, etc.).
SELECT
    c.nome_conjunto,
    COUNT(*) AS qtd_ocorrencias
FROM dados.ocorrencia o
JOIN dados.conjunto_eletrico c ON c.id_conjunto = o.id_conjunto
WHERE c.id_conjunto <> '0000000'
GROUP BY c.nome_conjunto
ORDER BY qtd_ocorrencias DESC
LIMIT 20;

-- 3) Quanto do total de ocorrências é "não identificado".
-- Mede a base de confiabilidade dos rankings acima: quanto do total não
-- tem município/conjunto real (ocorrências substitutas ou município fora
-- de PE).
SELECT
    COUNT(*) FILTER (WHERE id_municipio = '0000000') AS ocorrencias_sem_municipio,
    COUNT(*) FILTER (WHERE id_conjunto = '0000000') AS ocorrencias_sem_conjunto,
    COUNT(*) AS total_ocorrencias
FROM dados.ocorrencia;

-- 4) Cruzamento com consumidores afetados, por município.
-- Mostra não só quantas ocorrências, mas o impacto real em consumidores --
-- diferencia "muitas ocorrências pequenas" de "poucas ocorrências que
-- afetam muita gente".
SELECT
    m.nome_municipio,
    COUNT(DISTINCT o.id_ocorrencia) AS qtd_ocorrencias,
    SUM(i.consumidores_afetados) AS total_consumidores_afetados
FROM dados.ocorrencia o
JOIN dados.municipio m ON m.id_municipio = o.id_municipio
JOIN dados.interrupcao i ON i.id_ocorrencia = o.id_ocorrencia
WHERE m.id_municipio <> '0000000'
GROUP BY m.nome_municipio
ORDER BY total_consumidores_afetados DESC
LIMIT 20;
