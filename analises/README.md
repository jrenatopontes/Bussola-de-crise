# EDA — Bússola de Crise

Análise exploratória dos dados de ocorrências emergenciais da rede de distribuição em Pernambuco.

## O que foi analisado

* valores ausentes;
* causas de origem;
* causas específicas;
* canais de atendimento;
* duração das ocorrências;
* duração por causa;
* evolução mensal das ocorrências;
* tempos de preparo, deslocamento e execução;
* municípios com maior volume de ocorrências;
* distribuição e comportamento dos tempos de atendimento.

## Tratamento dos dados

* `dth_inicio` e `dth_fim` foram convertidas para o formato de data/hora;
* a duração das ocorrências foi calculada em minutos;
* os valores ausentes foram identificados e analisados;
* as variáveis de tempo foram utilizadas para analisar as etapas de atendimento;
* os dados foram utilizados para identificar padrões e características das ocorrências no período analisado.

## Período e base

A análise utiliza a base de ocorrências emergenciais da rede de distribuição, considerando os dados do período analisado no projeto.

Os resultados da EDA servem como etapa exploratória para identificar padrões, possíveis inconsistências e informações relevantes para as perguntas analíticas do projeto.
