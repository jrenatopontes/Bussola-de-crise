# Análise Exploratória de Dados: Interrupções e Ocorrências Emergenciais

## Escopo

Este relatório reúne os resultados das análises das bases de Interrupções e Ocorrências Emergenciais para **2021–2025**. O ano de 2026 foi excluído por incompletude dos campos. As bases representam unidades de análise diferentes: uma registra interrupções e a outra ocorrências/chamados; portanto, seus volumes são apresentados separadamente, sem somar os totais.

Foram analisados **1.109.874 registros de interrupções** e **1.844.779 ocorrências emergenciais**. As visualizações abaixo resumem a completude, as causas, a duração, a sazonalidade, a localização e o impacto ao consumidor.

![Painel geral da EDA de 2021 a 2025](figuras/painel_eda_2021-2025.png)

## 1. Completude e panorama das causas

Nos campos avaliados para o período, não foram encontrados valores ausentes. Isso inclui datas de início/fim, canal, município, tempos de atendimento e campos de consumidores afetados. A conclusão se limita às colunas verificadas nas tabelas staging; não significa que todas as variáveis da fonte original sejam completas.

Em **Interrupções**, a principal causa específica é **falha de material ou equipamento**, com 337.323 eventos (30,39%). Em seguida aparecem vento (110.712; 9,98%), árvore ou vegetação (101.935; 9,18%) e interferência de terceiros (96.183; 8,67%).

Em **Ocorrências Emergenciais**, 459.499 registros (24,91%) estão classificados como “não classificada”. Falha de material ou equipamento representa 435.299 (23,60%); árvore ou vegetação, 141.873 (7,69%); interferência de terceiros, 125.063 (6,78%); e vento, 117.214 (6,35%). A proporção de registros sem causa específica indica uma oportunidade de melhorar a classificação no atendimento.

## 2. Atendimento e duração

O canal “informação ou reclamação do consumidor ou de terceiros” concentra aproximadamente **98,2%** das ocorrências; registros automáticos do sistema de supervisão correspondem a cerca de 1,8%. Assim, o histórico é predominantemente formado por eventos percebidos e comunicados por consumidores ou terceiros.

Entre as **1.844.779 ocorrências com duração calculável**, a duração mediana é **296 minutos** (4h56), enquanto a média chega a **738 minutos** (12h18). O quartil inferior é 154 minutos e o superior, 824 minutos. A distância entre média e mediana mostra uma distribuição assimétrica, com uma cauda de atendimentos muito longos.

| Faixa de duração | Ocorrências | Participação aproximada |
|---|---:|---:|
| Até 30 minutos | 5.055 | 0,3% |
| 30 minutos a 2 horas | 293.499 | 15,9% |
| 2 a 6 horas | 743.623 | 40,3% |
| 6 a 24 horas | 594.402 | 32,2% |
| 24 horas ou mais | 208.200 | 11,3% |

Ao comparar a duração mediana por causa, os maiores valores aparecem em abalroamento (989 min; 9.272 registros), erosão (643 min; 5.195), desligamento por segurança (542 min; 2.733) e inundação (477 min; 999). São grupos menores que as causas mais frequentes e devem ser lidos como sinais para investigação, não como evidência de que a causa, isoladamente, determina o tempo de atendimento. A comparação considera categorias com pelo menos 100 registros.

## 3. Tempos das etapas de atendimento

Os três tempos têm 1.844.779 valores válidos no recorte. A **preparação** apresenta a maior mediana: 144,52 minutos, contra 37,30 na execução e 31,08 no deslocamento. As médias são 398,53, 300,33 e 39,47 minutos, respectivamente. A diferença expressiva entre média e mediana, sobretudo em preparação e execução, sugere que poucos casos muito longos elevam as médias; para representar o atendimento típico, a mediana é mais informativa.

## 4. Evolução mensal e sazonalidade causal

Para 2021–2025, a evolução mensal foi derivada das datas de início. Os nomes `NumAnoCompetencia` e `NumMesCompetencia` não estão disponíveis nos schemas antigos carregados; por isso, ano e mês foram extraídos das datas. Nos arquivos desse período, os quatro níveis de causa estão concatenados nas descrições e foram reconstruídos para a análise.

O índice sazonal do gráfico é normalizado por causa e ano: **1 representa a média mensal daquela causa**; valores acima de 1 indicam concentração relativa maior naquele mês. Nas Interrupções, descargas atmosféricas atingem seu pico médio em março (índice 1,78), e vento também tem pico em março (1,32). Árvore ou vegetação tem maior concentração relativa em maio nas duas bases (1,25 em Interrupções e 1,37 em Ocorrências Emergenciais).

![Sazonalidade das causas em Interrupções e Ocorrências Emergenciais](figuras/sazonalidade_causas_2021-2025.png)

Esses padrões ajudam a programar inspeções e disponibilidade de equipes antes dos períodos de maior incidência. O alinhamento com chuva, vento ou descargas atmosféricas é uma hipótese operacional: para afirmar relação climática, é necessário cruzar a série com dados meteorológicos.

## 5. Municípios e dificuldade logística

Por volume de ocorrências emergenciais, Recife lidera (279.032), seguido por Jaboatão dos Guararapes (108.271), Petrolina (74.700), Olinda (71.068) e Paulista (64.678). Esse ranking mede número de registros, não quantidade de consumidores únicos.

Para deslocamentos positivos, foi aplicado o limite de outlier de Tukey, **Q3 + 1,5 × IQR = 105,77 minutos**. Foram encontrados 74.601 deslocamentos acima do limite entre 1.844.760 tempos positivos válidos. Entre os municípios com ao menos 30 registros, as maiores proporções são Santa Filomena (26,84%), Manari (26,49%), Moreilândia (25,37%) e Carnaubeira da Penha (23,66%). O indicador aponta concentração de viagens excepcionalmente longas, não identifica sozinho a causa logística.

## 6. Severidade e prioridade de infraestrutura

A severidade de cada interrupção foi definida pela distribuição de unidades consumidoras afetadas: baixa até P50 (1 UC), moderada até P75 (24 UCs), alta até P95 (402 UCs) e crítica acima do P95. No recorte, 612.367 eventos são baixos, 223.264 moderados, 218.790 altos e 55.453 críticos. Os eventos críticos representam cerca de **5,0% dos registros**, mas somam aproximadamente **92,6 milhões de UCs-evento**.

Esse total é a soma de consumidores afetados em cada evento e **não** corresponde a consumidores distintos: uma mesma unidade pode aparecer em várias interrupções.

Ordenando a infraestrutura pelo volume somado de UCs em eventos acima do P75, Pau Amarelo lidera entre as subestações (2.453.917 UCs-evento); entre os alimentadores, LJD-01L2 lidera (741.670). Seguem-se São Benedito (2.334.070) e Campus (2.016.579) no ranking de subestações; VCA-01C2 (623.457) e GVD-01J5 (590.269) no de alimentadores.

O staging disponível não contém `CodSubestacao` nem `CodAlimentador`; os rankings usam as descrições de subestação e alimentador presentes na fonte. As somas devem ser interpretadas como impacto acumulado por evento, não como clientes únicos ou capacidade instalada.

## Síntese para planejamento

1. Preparar equipes e inspeções para falhas de equipamento, a causa mais frequente nas interrupções.
2. Antecipar ações para árvores/vegetação antes de maio e acompanhar vento e descargas atmosféricas, com reforço em março; validar as hipóteses com séries climáticas locais.
3. Rever tempos e procedimentos de preparação, que têm a maior mediana entre as etapas de atendimento.
4. Usar os outliers de deslocamento para revisar cobertura e posicionamento de equipes em Santa Filomena, Manari e Moreilândia.
5. Considerar Pau Amarelo e o alimentador LJD-01L2 como candidatos a investigação preventiva, validando a prioridade com recorrência, criticidade e contexto operacional.

## Notas metodológicas

- Todas as análises deste relatório excluem 2026.
- Frequências de Interrupções e Ocorrências Emergenciais são mantidas separadas por terem granularidades diferentes.
- Canais, causas, município e duração foram calculados sobre registros disponíveis nas tabelas staging.
- Contagens de consumidores afetados somam ocorrências repetidas ao longo do período e não representam consumidores únicos.
- A análise sazonal identifica concentração temporal, mas não estabelece causalidade meteorológica.