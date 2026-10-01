# Pergunta 4 do canvas — Tempo de atendimento

**Pergunta:** "Quanto tempo: qual a duração de cada etapa do atendimento (preparo, deslocamento e execução) e onde esse tempo é pior?"

**Base analisada:** `dados.ocorrencia`, de 2021 a 2025. São 852.674 ocorrências com tempo registrado.

**Recorte:** a análise usa só as ocorrências emergenciais da Celpe que tiveram pelo menos uma interrupção registrada na base de Interrupções da ANEEL, cerca de 54% das ocorrências do período. As ocorrências substitutas (interrupções sem ocorrência casada) não entram, porque não têm tempo. Ver a seção "Limitações" no fim.

**Unidade:** todos os tempos estão em minutos, como na fonte. A duração total de cada atendimento é a soma das três etapas.

---

## 1. O que cada etapa mede

O dicionário de dados da ANEEL diz só que os três tempos estão em minutos. A definição de onde cada etapa começa e termina está no PRODIST, Módulo 8, Seção 8.2 (item 161):

- **Preparação:** do conhecimento da ocorrência pela distribuidora até a autorização para a equipe se deslocar. Inclui a espera por equipe disponível.
- **Deslocamento:** da autorização até a chegada da equipe ao local.
- **Execução:** da chegada da equipe até o restabelecimento do serviço.

Os indicadores oficiais TMP, TMD e TME são as médias de cada etapa, e o TMAE é a soma das três. Por isso a tabela da seção 2 mostra a média ao lado da mediana.

Que as colunas da base sigam exatamente essas definições é uma dedução nossa: os nomes batem, a fonte é a mesma ANEEL e a soma das etapas dá a duração do atendimento. A definição foi consultada numa cópia do PRODIST fora do site da ANEEL e ainda precisa ser conferida no PDF oficial.

## 2. Pernambuco, 2021 a 2025

| Etapa | Média (min) | Mediana (min) | Parcela do tempo total |
| --- | --- | --- | --- |
| Preparo | 322,8 | 125,1 | 50,2% |
| Deslocamento | 41,7 | 33,5 | 6,5% |
| Execução | 278,8 | 46,9 | 43,3% |
| **Duração total** | **643,3** | **274,0** | 100% |

- Um atendimento típico (mediana) leva **274 min, cerca de 4h34**. O preparo sozinho leva 2h05. As medianas das etapas não somam a mediana total, e isso é normal.
- Em média, o atendimento leva **643 min, cerca de 10h43**. É a medida comparável ao TMAE oficial.
- **O preparo é a maior etapa** no atendimento típico e responde por metade de todo o tempo gasto.
- **A execução tem a cauda mais longa:** a média é quase 6 vezes a mediana. A maior parte dos atendimentos é resolvida em menos de uma hora no local, mas poucos casos muito longos puxam a média para cima e fazem a execução pesar 43% do tempo total.
- **O deslocamento é curto e estável:** a média fica perto da mediana.

## 3. O padrão se repete todo ano?

| Ano | Ocorrências | Preparo | Deslocamento | Execução | Mediana total | Média total |
| --- | --- | --- | --- | --- | --- | --- |
| 2021 | 152.674 | 114,0 | 35,4 | 49,4 | 270,0 | 655,7 |
| 2022 | 161.349 | 125,0 | 34,2 | 50,0 | 284,9 | 771,2 |
| 2023 | 157.369 | 120,3 | 33,4 | 45,7 | 267,8 | 669,8 |
| 2024 | 180.650 | 128,7 | 33,5 | 46,6 | 278,1 | 637,2 |
| 2025 | 200.632 | 134,0 | 31,8 | 44,5 | 270,7 | 515,6 |

As colunas de etapa são medianas, em minutos.

- **A mediana total quase não muda:** fica entre 268 e 285 min (4h28 a 4h45) nos cinco anos.
- **O preparo cresce:** de 114 min em 2021 para 134 em 2025 (+20 min, +17,5%). A subida não é contínua (2023 fica abaixo de 2022), mas a tendência do período é de alta.
- **Deslocamento e execução caem um pouco:** cerca de −10% cada no período.
- Na mediana, o preparo maior foi compensado pelo deslocamento e pela execução menores, e por isso o total ficou estável.
- **A média total varia bem mais que a mediana:** 771 min em 2022 e 516 em 2025. Isso indica que a quantidade de atendimentos muito longos muda de um ano para outro.
- Isto descreve o período, não explica. Os dados não dizem por que o preparo cresceu.

## 4. Onde o tempo é pior: municípios

Os 20 municípios com maior mediana de duração total no período (todos com mais de 30 ocorrências). Em Pernambuco, as medianas são: preparo 125,1 · deslocamento 33,5 · execução 46,9 · total 274,0.

| # | Município | Ocorrências | Preparo | Desloc. | Execução | Mediana total | Média total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Arcoverde | 8.722 | 150,9 | 38,5 | **79,0** | 518,1 | 1.416,6 |
| 2 | Santa Filomena | 1.959 | **297,3** | **70,7** | 32,7 | 488,1 | 911,6 |
| 3 | Tupanatinga | 2.773 | **285,6** | **65,2** | 46,4 | 474,0 | 883,3 |
| 4 | Inajá | 2.913 | **276,9** | **54,2** | 35,8 | 473,0 | 883,7 |
| 5 | Dormentes | 2.734 | **279,5** | **54,7** | 38,9 | 467,1 | 879,4 |
| 6 | São Benedito do Sul | 1.088 | **235,3** | **63,5** | **67,4** | 466,9 | 938,2 |
| 7 | Manari | 1.818 | **286,8** | **59,4** | 34,5 | 466,6 | 922,5 |
| 8 | Carnaubeira da Penha | 1.533 | **228,2** | **66,6** | 38,0 | 456,4 | 819,7 |
| 9 | Granito | 1.295 | **266,7** | **67,2** | 37,8 | 454,0 | 817,5 |
| 10 | Moreilândia | 1.494 | **242,9** | **68,5** | 38,5 | 449,2 | 886,9 |
| 11 | Poção | 1.440 | **264,9** | **56,2** | 49,5 | 444,3 | 878,5 |
| 12 | Parnamirim | 2.468 | **221,0** | **67,6** | 39,9 | 431,9 | 799,6 |
| 13 | Belém do São Francisco | 2.404 | **201,3** | **62,8** | 44,0 | 430,9 | 841,8 |
| 14 | Santa Cruz | 2.398 | **267,1** | **62,7** | 33,3 | 428,7 | 786,5 |
| 15 | Exu | 4.079 | **226,6** | **58,2** | 41,6 | 428,7 | 848,1 |
| 16 | Ouricuri | 9.223 | 159,3 | 43,9 | 51,3 | 427,8 | 1.348,1 |
| 17 | Belo Jardim | 10.038 | 156,2 | 35,5 | **63,0** | 427,0 | 1.379,9 |
| 18 | Afrânio | 3.005 | **254,5** | 47,4 | 37,3 | 418,5 | 806,4 |
| 19 | Belém de Maria | 1.125 | 192,8 | **52,8** | **60,9** | 408,6 | 883,2 |
| 20 | Maraial | 962 | 187,7 | **56,8** | **72,6** | 402,9 | 1.018,4 |

Os tempos estão em minutos. Em negrito: preparo de 200 min ou mais, deslocamento de 50 min ou mais e execução de 60 min ou mais (cerca de 1,3 a 1,6 vez a mediana do estado).

- **Nos 20 municípios, o preparo e o deslocamento ficam acima da mediana do estado.** Em 15 deles, o preparo passa de 200 min, de 1,6 a 2,4 vezes o estado. Em 16, o deslocamento passa de 50 min. Santa Filomena tem o maior preparo (297 min, 2,4 vezes o estado) e o maior deslocamento (71 min, 2,1 vezes).
- **Um segundo grupo se destaca pela execução, não pelo preparo:** Arcoverde (79 min, 1,7 vez o estado), Maraial, São Benedito do Sul, Belo Jardim e Belém de Maria.
- **Arcoverde, Ouricuri e Belo Jardim são casos à parte.** Eles têm muito mais ocorrências que os outros (8,7 mil a 10 mil) e preparo próximo do estado (151 a 159 min), mas a média total passa de 22 horas (1.348 a 1.417 min). A mediana já é alta e a cauda de atendimentos longos é muito pesada.
- **Leitura, ainda não verificada:** a maioria desses municípios é do Sertão e do Agreste. Três são da Mata Sul (São Benedito do Sul, Maraial e Belém de Maria). Preparo e deslocamento longos combinam com municípios distantes das bases das equipes, mas isso é hipótese, não causa demonstrada.

**Comparação com a análise de 2025 no Colab** (todas as ocorrências, um ano): 16 destes 20 municípios estavam no núcleo de "piores no ano e sistematicamente piores", e 2 estavam no grupo "sinal forte, pouco dado" (São Benedito do Sul e Maraial). Os novos são Dormentes e Afrânio. Com recortes e períodos diferentes, as duas análises apontam quase os mesmos lugares, e isso deixa o resultado mais sólido.

## 5. Onde o tempo é pior: conjuntos elétricos

Os 20 conjuntos com maior mediana de duração total no período. O nome vem da base de Interrupções.

| # | Código | Conjunto | Ocorrências | Preparo | Desloc. | Execução | Mediana total | Média total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14122 | Barragem do Prata | 295 | 183,1 | 53,9 | **98,9** | 534,4 | 1.527,8 |
| 2 | 15657 | Afrânio | 1.046 | **263,9** | 56,1 | 37,0 | 531,6 | 1.047,9 |
| 3 | 16153 | Santa Cruz | 6.575 | **275,0** | 66,1 | 36,8 | 485,1 | 989,6 |
| 4 | 15658 | Rajada | 649 | **238,3** | **84,0** | 36,2 | 484,7 | 838,2 |
| 5 | 14125 | Belém de São Francisco | 370 | **212,0** | 54,0 | **60,5** | 459,3 | 1.077,1 |
| 6 | 14157 | Exu | 7.342 | **218,9** | 58,6 | 44,4 | 457,3 | 1.037,6 |
| 7 | 14146 | Caraíbas II | 215 | 166,8 | 61,7 | 46,6 | 454,2 | 1.091,2 |
| 8 | 16186 | Parnamirim | 4.539 | **201,3** | 62,7 | 43,5 | 438,3 | 1.017,1 |
| 9 | 16733 | Afrânio | 6.313 | **242,4** | 54,2 | 39,8 | 438,1 | 932,2 |
| 10 | 16179 | Buíque | 10.026 | **240,2** | 56,7 | 47,2 | 430,8 | 867,2 |
| 11 | 16736 | Cabrobó | 4.038 | 191,2 | 64,0 | 41,8 | 428,7 | 902,0 |
| 12 | 16165 | Floresta | 6.588 | **205,0** | 60,7 | 38,8 | 417,0 | 849,9 |
| 13 | 14171 | Inajá | 6.894 | **230,2** | 55,7 | 39,3 | 412,1 | 867,8 |
| 14 | 14152 | Correntes | 4.263 | 191,3 | 53,1 | **57,7** | 400,9 | 935,0 |
| 15 | 14121 | Barra de Bebedouro | 5.870 | 196,2 | 55,2 | 43,8 | 393,1 | 847,7 |
| 16 | 14132 | Bonito | 3.509 | 172,8 | 43,6 | **61,2** | 387,5 | 1.038,4 |
| 17 | 14174 | Itaparica | 2.978 | **207,3** | 49,1 | 37,7 | 387,4 | 812,6 |
| 18 | 16181 | Pesqueira | 8.900 | 195,0 | 48,0 | **53,1** | 385,3 | 860,3 |
| 19 | 14140 | Cabrobó | 569 | 138,5 | 68,4 | **51,6** | 376,7 | 1.015,5 |
| 20 | 16177 | Quipapá | 6.827 | 169,9 | 51,8 | **63,1** | 375,4 | 823,7 |

Os tempos estão em minutos. Em negrito: preparo de 200 min ou mais, deslocamento de 80 min ou mais e execução acima de 50 min.

- **O padrão dos municípios se repete:** nos 20 conjuntos, o preparo (138 a 275 min) e o deslocamento (44 a 84 min) ficam acima da mediana do estado.
- **Rajada tem o maior deslocamento da lista:** 84 min, 2,5 vezes o estado.
- **Barragem do Prata tem a maior execução:** 99 min, 2,1 vezes o estado, e a maior média total (1.528 min, cerca de 25h28). São só 295 ocorrências em cinco anos.
- **Vários lugares aparecem nas duas listas,** de municípios e de conjuntos: Santa Cruz, Exu, Parnamirim, Afrânio, Inajá, Belém do São Francisco e Cabrobó.
- **Afrânio e Cabrobó aparecem duas vezes cada, com códigos diferentes** (15657 e 16733; 16736 e 14140). Os códigos menos frequentes têm poucas ocorrências no período. Hipótese ainda não verificada: a ANEEL pode ter trocado o código desses conjuntos no meio do período, e aí a mesma área aparece dividida em dois códigos. Isso precisa ser conferido ano a ano antes de apresentar os conjuntos menores.

## 6. Conclusão

- **Um atendimento típico em Pernambuco leva cerca de 4h30**, e esse valor ficou estável de 2021 a 2025.
- **O preparo é a etapa que mais pesa e a que mais cresceu.** Ele ocupa metade do tempo total de atendimento, e a mediana subiu 17,5% no período. Pela definição do PRODIST, é o tempo até a equipe ser autorizada a sair, o que inclui a espera por equipe disponível.
- **A execução quase sempre é curta, mas tem casos extremos** que puxam a média para mais de 4 horas.
- **Os lugares com pior tempo combinam preparo e deslocamento longos** e parecem se concentrar no Sertão e no Agreste, o que ainda falta confirmar com a mesorregião do IBGE. Arcoverde, Belo Jardim, Ouricuri, Maraial e Barragem do Prata destoam pela execução longa.
- **Para a decisão do gestor de plantão:** nos lugares em que o deslocamento é longo, a antecipação de deslocamento tem mais espaço para reduzir tempo. Onde o problema é o preparo, a questão parece ser a disponibilidade de equipe. Isso é leitura do diagnóstico, não resultado testado.

## 7. Limitações

- **Recorte:** a análise cobre só as ocorrências com pelo menos uma interrupção registrada, cerca de 54% do total. Por isso, os números não batem com a análise de 2025 feita no Colab com todas as ocorrências. Em 2025, o recorte quase não muda a mediana total (270,7 contra 271,2 min), mas muda as etapas: preparo 134,0 contra 151,6 e execução 44,5 contra 34,0.
- **Conjunto elétrico:** em `dados.ocorrencia`, o conjunto vem da primeira interrupção ligada à ocorrência. Em cerca de 2% das interrupções, a mesma interrupção aparece em mais de um conjunto, e só o primeiro fica no banco.
- **Ranking do período todo:** as tabelas mostram quem tem a pior mediana nos cinco anos somados. Não mostram se o lugar é ruim todo mês. Esse critério de "sistematicamente pior" só foi aplicado em 2025, no Colab.
- **Municípios com pouco dado:** Maraial (962 ocorrências) e São Benedito do Sul (1.088) têm bem menos dados que os municípios grandes. Na lista de conjuntos, Barragem do Prata, Caraíbas II, Belém de São Francisco, Rajada e Cabrobó (14140) têm menos de 700 ocorrências em cinco anos.
- **Ocorrências fora de PE:** ocorrências com código IBGE fora de PE ficam no município "Não identificado" e saem do ranking por município. Entram no cálculo do estado e no ranking por conjunto.
- **Diagnóstico, não previsão:** a análise descreve onde e quanto o atendimento demorou de 2021 a 2025. Ela não explica as causas nem prevê o que vai acontecer.
