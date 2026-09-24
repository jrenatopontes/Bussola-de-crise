Canvas do Projeto — M6 Experiência Prática
Como usar: copie este arquivo para docs/canvas-projeto.md no repositório da equipe e preencha durante o E2 (qua 16/09). O canvas é validado pelo mentor ao fim do E2: aprovado, aprovado com ajustes, ou devolvido com pendências claras (pendências resolvidas até o E3). O canvas aprovado fica versionado no repositório — ele é a referência dos checkpoints: as perguntas daqui são as que o CP1 verifica (critério 1.4) e as que a análise e o dashboard precisam responder (critérios 2.1 e 2.2).
Lembre da regra do E2: não existe viabilidade sem amostra baixada e aberta.
## Identificação

|  |  |
| --- | --- |
| Nome da equipe | Bússola de Crise |
| Integrantes | Visualização - Nilda Modelagem - Rhayane SM - Danilo QA - Amanda Dados  - Cauê PO/Analista - Renato PO/Analista - Maysa pitch - Vitor |
| Mentor | Danilo e Deni |
| Tema |  |
| Repositório GitHub | https://github.com/jrenatopontes/Bussola-de-crise |

## 1. Problema de negócio
A Neoenergia precisa decidir onde priorizar e deslocar suas equipes de campo diante de interrupções e quedas de energia, buscando reduzir o tempo de atendimento e o impacto para os consumidores. Atualmente, essa decisão pode ser aprimorada com a identificação dos pontos críticos e dos padrões históricos de ocorrências, permitindo antecipar regiões com maior probabilidade de interrupções e direcionar os recursos de forma mais eficiente.
## 2. Público / decisor
Gestor de plantão do Centro de Operações da Neoenergia PE
## 3. Perguntas analíticas

| # | Pergunta | Que decisão ela informa? | Respondível com os dados? (verificado na amostra) |
| --- | --- | --- | --- |
| 1 | Onde se concentram as ocorrências emergenciais em Pernambuco: quais municípios e conjuntos elétricos registram o maior volume? | Orienta o planejamento geográfico. Informa decisões de alocação de investimentos em infraestrutura, abertura ou remanejamento de bases operacionais e redistribuição estratégica das equipes de campo para as áreas críticas. | Sim |
| 2 | Quando elas acontecem: existe alguma sazonalidade ao longo dos meses ou uma concentração em horários específicos do dia? | Orienta a gestão de escala e dimensionamento. Informar decisões de planejamento de turnos, definição de sobreavisos, contratação temporária em períodos críticos (como épocas de chuva) e programação de manutenções preventivas para períodos de baixa demanda. | Sim |
| 3 | Por que elas acontecem: quais são as causas mais frequentes e quais delas demandam mais tempo para solução? | Orienta a manutenção preventiva e engenharia. Informa decisões de priorização de investimentos (ex.: poda de árvores vs. substituição de equipamentos antigos), treinamentos específicos para causas complexas e revisões de contratos de fornecedores. | Sim |
| 4 (opcional) | Quanto tempo leva o atendimento: qual é a duração média de cada etapa (preparo, deslocamento e execução) e em quais municípios ou conjuntos esse tempo é sistematicamente pior? | Orienta a eficiência operacional e logística. Informa decisões de otimização de rotas, melhoria nos processos internos de despacho e Revisão de metas de nível de serviço (SLA). | Sim |
| 5 (opcional) | Existe relação entre as ocorrências de interrupção e determinadas condições climáticas? | Informa os períodos e regiões que apresentam maior recorrência de interrupções associadas a condições climáticas, contribuindo para a priorização e o planejamento do atendimento das equipes. |  |

## 4. Fontes de dados
Uma linha por fonte. A amostra precisa ter sido baixada e aberta hoje — coluna a coluna. Lembrete: se a fonte tiver API, a coleta usa API (requisito do M3). Troca de fonte é livre até o E3 (21/09); depois, só com a coordenação.

| Fonte | Link | Formato | Volume estimado | Licença/acesso | Amostra baixada e aberta? (sim/não) | Colunas-chave confirmadas na amostra |
| --- | --- | --- | --- | --- | --- | --- |
| ANEEL — Ocorrências Emergenciais nas Redes de Distribuição | http://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao | Parquet e Dbeaver | 376.739 linhas em PE em 15 colunas | Pública | Sim | CodIBGE, DthInicioOcorrenciaAberta, DthFimOcorrenciaAberta, DscOcorrenciaAberta, MdaPreparo, MdaDeslocamento, MdaExecucao, IdeConjUndConsumidoras, NomAgente |
|  |  |  |  |  |  |  |

## 5. Escopo e entregáveis — a regra do fatiável
Defina primeiro a fatia mínima: o menor recorte que ainda exercita o ciclo completo (banco → pipeline → análise → dashboard). Ela é o compromisso da equipe. As extensões só entram se a fatia mínima estiver pronta — e nada entra após o congelamento de escopo (05/10).
### Fatia mínima (compromisso):
Ocorrências de interrupção e queda de energia na área de atuação da Neoenergia Pernambuco, considerando um período histórico de 5 anos completos e o primeiro semestre do ano de 2026 dos dados, com organização dos dados em banco/pipeline, identificação dos principais pontos críticos e padrões de ocorrência e dashboard para acompanhamento da distribuição, frequência e características das interrupções.
### Extensões desejáveis (apenas se sobrar tempo):
Análise de recorrência por região e/ou localização; (ex: Região metropolitana; Zona da Mata; Agreste e Sertão)
Cruzamento com a base de dados de clima;
### Fora de escopo (o que decidimos NÃO fazer):
Utilizar dados de outros estados;
Previsão em tempo real das interrupções;
Automação do despacho ou deslocamento das equipes;
Controle operacional direto das equipes de campo;
## 6. Riscos e mitigação
Ao menos 3 riscos do seu projeto (não genéricos). Consulte a tabela de riscos comuns no guia-do-projeto.md.

| Risco | Sinal precoce | Mitigação | Responsável por monitorar |
| --- | --- | --- | --- |
| Dependência de uma pessoa técnica | Concentração de tarefas complexas em um único membro ou falta de visibilidade sobre as entregas dos demais. | "Todos codificam" verificado nos checkpoints; prova de reprodutibilidade na máquina de outro integrante; rodízio do daily | Danilo Galindo (SM) |
| Escopo grande demais | Dificuldade em fechar os incrementos do projeto dentro do prazo do checkpoint. | Regra do fatiável no canvas; corte no CP1 preserva o ciclo completo | Danilo Galindo (SM) |
| Perfeccionismo no dashboard | Foco excessivo em detalhes visuais e customizações antes das funcionalidades essenciais estarem prontas. | Dia fixo (E8), dados já no banco desde o CP1, mantra "feio funcionando antes de bonito", teste do usuário leigo | Danilo Galindo (SM) |
| Dados históricos insuficientes ou disponíveis apenas para parte do período | Muitas células vazias dentro de um mesmo período de tempo | Definir o período final de acordo com a disponibilidade e qualidade dos dados | Cauê Lima / Rhayane Leão |
| Inconsistências na identificação das zonas ou localizações mais precisas | Dados com informações partidas | Padronizar os campos e realizar validações durante o pipeline | Cauê Lima / Rhayane Leão |
| Dados incompletos ou com valores ausentes | Muitas células vazias | Realizar tratamento, validação e documentação dos dados antes das análises | Cauê Lima / Rhayane Leão |

## 7. Divisão de papéis
Todos codificam — papéis distribuem responsabilidade de acompanhamento, não exclusividade de execução. Cada papel tem uma pessoa sombra (backup). Em equipes de 4, coordenação acumula com outro papel; em equipes de 5–6, dados/pipeline e análise podem ser duplicados.

| Papel | Titular | Sombra |
| --- | --- | --- |
| Coordenação de projeto | Danilo Galindo |  |
| Dados / pipeline | Cauê Lima / Rhayane Leão |  |
| Análise | José e Maysa Guedes |  |
| Visualização / pitch | Nilda Juliana / Vitor |  |
| QA (Controle de Qualidade) | Amanda |  |

Canal de comunicação da equipe (fora do horário de aula):
Grupo do Whatsapp + Trello
Validação do mentor (preenchida pelo mentor no E2)

|  |  |
| --- | --- |
| Status | ( ) Aprovado ( ) Aprovado com ajustes ( ) Devolvido com pendências |
| Data | 16/09/2026 |
| Amostra baixada e aberta verificada? | ( ) Sim ( ) Não |
| Pendências (com prazo até o E3 — seg 21/09) |  |
