# EDA — Bússola de Crise

Análise exploratória da amostra de ocorrências.

## O que foi analisado
- valores ausentes;
- causas de origem;
- causas específicas;
- canais de atendimento;
- duração das ocorrências;
- duração por causa;
- evolução mensal;
- tempos de preparo, deslocamento e execução;
- municípios com mais ocorrências.

## Tratamento
`dth_inicio` e `dth_fim` foram convertidas para data/hora.
A duração foi calculada em minutos.
Valores ausentes em `causa_especifica` foram mantidos como ausentes.

## Observação
A base contém uma amostra de 500 ocorrências. Os resultados representam essa
amostra e o período disponível.
