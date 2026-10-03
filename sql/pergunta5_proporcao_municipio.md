# Pergunta 5 (clima): complemento sobre Petrolina

**Contexto:** a análise da pergunta 5 aponta Petrolina como o município "mais afetado por
causas climáticas", com base no volume bruto de ocorrências climáticas (vento, descarga
atmosférica, inundação, vegetação) por município.

**Observação:** Petrolina também está entre os municípios com maior volume de ocorrências
no geral (todas as causas, não só climáticas) — ela já aparece entre os 5 maiores na
análise da pergunta 1. Isso sugere que vale complementar a leitura olhando a **proporção**
de ocorrências climáticas sobre o total de cada município, não só o volume absoluto —
assim conseguimos distinguir "município com clima proporcionalmente mais dominante" de
"município com mais ocorrências de tudo, inclusive clima".

## Consulta usada

```sql
WITH clima AS (
    SELECT o.id_municipio, COUNT(*) AS qtd_clima
    FROM dados.ocorrencia o
    JOIN dados.causa c ON c.id_causa = o.id_causa
    WHERE c.detalhe_causa ILIKE ANY (ARRAY['%VENTO%', '%DESCARGA ATMOSF%', '%INUNDA%', '%VEGETA%'])
      AND o.id_municipio <> '0000000'
      AND o.inicio_ocorrencia < '2026-01-01'
    GROUP BY o.id_municipio
),
total AS (
    SELECT o.id_municipio, COUNT(*) AS qtd_total
    FROM dados.ocorrencia o
    WHERE o.id_municipio <> '0000000'
      AND o.inicio_ocorrencia < '2026-01-01'
    GROUP BY o.id_municipio
)
SELECT m.nome_municipio, t.qtd_total, cl.qtd_clima,
       ROUND(100.0 * cl.qtd_clima / t.qtd_total, 1) AS pct_climatico
FROM total t
JOIN clima cl ON cl.id_municipio = t.id_municipio
JOIN dados.municipio m ON m.id_municipio = t.id_municipio
WHERE t.qtd_total >= 1000
ORDER BY pct_climatico DESC
LIMIT 20;
```

## Resultado

Por proporção, Petrolina não aparece entre os 20 primeiros. Os municípios em que o clima
representa a maior fatia das ocorrências são outros:

| Município | Ocorrências totais | Ocorrências climáticas | % climático |
|---|---|---|---|
| Santa Cruz | 2.398 | 1.663 | 69,3% |
| Santa Filomena | 1.959 | 1.333 | 68,0% |
| Granito | 1.295 | 876 | 67,6% |
| Bodocó | 5.077 | 3.293 | 64,9% |
| Parnamirim | 2.468 | 1.565 | 63,4% |
| Exu | 4.079 | 2.561 | 62,8% |
| Moreilândia | 1.494 | 934 | 62,5% |

(lista completa com 20 municípios disponível na consulta acima)

## Sugestão de complemento para o relatório

As duas leituras são válidas e se complementam:

- **Em volume absoluto**, Petrolina lidera — relevante para dimensionar o esforço total
  de resposta a causas climáticas.
- **Em proporção**, municípios como Santa Cruz, Santa Filomena e Granito se destacam —
  mais de 65% das ocorrências neles têm causa climática, o que os torna candidatos
  fortes para ações preventivas específicas de clima (poda, reforço de rede antes de
  temporais), já que ali o clima não é "mais uma causa entre várias", é o fator
  dominante.


## Apenas sugestão se vocês acharem um dado importante.