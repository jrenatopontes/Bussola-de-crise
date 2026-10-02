
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