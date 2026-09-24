# Banco de dados — Bússola de Crise (2021-2025 + 1º sem. 2026)

Documentação do banco `bussola_de_crise` (PostgreSQL), que organiza as ocorrências de interrupção de energia da Neoenergia PE entre 2021 e 2025 (5 anos completos) mais o 1º semestre de 2026.

> ✅ **Status em 22/09: pipeline completo fim a fim.** Staging carregado para todos os 6 anos (2021-2026) e as 5 tabelas de `dados.*` populadas e validadas — ver contagens e as 3 correções de integridade encontradas hoje logo abaixo.

> ✅ **Status em 23/09: extensão INMET concluída.** Schema, carga do staging e transformação do INMET (clima) prontos e rodados para os 6 anos. Ver seção "Extensão INMET" mais abaixo.

**Contagens finais validadas:**

| Tabela | Linhas |
|---|---|
| `dados.municipio` | 186 (185 de PE + 1 sentinela) |
| `dados.causa` | 76 (75 causas distintas + 1 sentinela) |
| `dados.conjunto_eletrico` | 169 (168 + 1 sentinela) |
| `dados.ocorrencia` | 1.078.022 (994.215 reais + 83.807 substitutas) |
| `dados.interrupcao` | 3.008.002 |

Casamento interrupção ↔ ocorrência no conjunto completo: **97,2% (2.924.195 de 3.008.002)**.

**Contagens do INMET** (banco local, 23/09):

| Tabela | Linhas |
|---|---|
| `staging.inmet_estacao` | 75 (estação × ano) |
| `staging.inmet_horario` | 604.584 |
| `dados.estacao` | 75 |
| `dados.clima_diario` | 25.180 |
| `dados.municipio_estacao` | 3.330 (185 municípios × 6 anos × 3 estações) |

## Fontes de dados

1. **ANEEL — Ocorrências Emergenciais nas Redes de Distribuição**
   https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao
   Única fonte com início/fim da **ocorrência** e os tempos de preparo, deslocamento e execução do atendimento.
2. **ANEEL — Interrupções de Energia Elétrica nas Redes de Distribuição**
   https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao
   Fonte de município, causa (já em 4 níveis), conjunto elétrico (nome + total de consumidores) e consumidores afetados.
3. **INMET — Dados históricos**
   https://portal.inmet.gov.br/dadoshistoricos
   Dados de clima das estações automáticas de PE (1 ZIP por ano, 1 CSV por estação). Entra no banco como extensão do modelo (3 tabelas em `dados.*`, ver seção "Extensão INMET"). Serve para a pergunta sobre relação entre ocorrências e clima — **relação, não causa**.

Todos os arquivos das duas fontes ANEEL são nacionais e precisam de filtro pelo nome do agente contendo "PERNAMBUCO" (Neoenergia PE / Celpe) antes de entrar no banco — atenção: **o nome da coluna de filtro é diferente em cada fonte** (`NomAgente` em Ocorrências Emergenciais, `NomAgenteRegulado` em Interrupções no schema antigo — no schema novo de 2026, ambas as fontes usam `NomAgente`).

As duas fontes ANEEL são ligadas pela mesma ocorrência:
- `NumOcorrencia` (Ocorrências Emergenciais) = primeira parte de `NumOrdemInterrupcao` **antes do `_`** (Interrupções) — `NumOrdemInterrupcao` vem no formato `"{num_ocorrencia}_{id_interrupcao}"`.

> ⚠️ **Correção em 22/09 (validada com dados reais da Neoenergia PE)**: o dicionário de dados da ANEEL usado inicialmente para desenhar o mapeamento abaixo não batia com os arquivos reais baixados — no schema de 2021-2025 não existem `CodOcorrencia`/`CodInterrupcao`/`CodMunicipioIBGE` no arquivo de Interrupções, nem causa em 4 colunas separadas (vem em 1 coluna só, hífen-delimitada). Uma primeira tentativa de validar a chave `NumOcorrencia = NumOrdemInterrupcao` direto (sem split) deu **0% de casamento** nos dados reais da Neoenergia PE — a amostra que parecia confirmar isso antes era de outra distribuidora, coincidência de formato. Comparando os valores reais da Neoenergia PE, descobrimos que `NumOrdemInterrupcao` é composto (`"16840968_15717123"`, por exemplo) e que a parte antes do `_` é a chave da ocorrência. Com essa correção, **92,7% das interrupções (178.618 de 192.644) casam** com uma ocorrência — validado com o carregamento completo de 2021. Com todos os 6 anos juntos, o casamento sobe para **97,2%**.

> ⚠️ **2026: ANEEL redesenhou o schema das duas fontes.** A partir do arquivo de 2026, `Ocorrências Emergenciais` passou a trazer os campos de tempo (`MdaPreparo`/`MdaDeslocamento`/`MdaExecucao`) como string vazia (`''`) em vez de `NULL` quando o atendimento não foi finalizado, e `Interrupções` ganhou um schema totalmente novo (`CodOcorrencia`/`CodInterrupcao` voltam a existir como colunas separadas, e a causa vem em 4 colunas: `DscFatoGeradorOrigem/Tipo/Causa/Detalhe`). `carregar_staging_aneel.py` detecta automaticamente qual schema o arquivo tem e reconstrói `NumOrdemInterrupcao` e a causa concatenada no formato antigo, para o resto do pipeline continuar funcionando sem mudanças.

## Modelo de dados

5 entidades:

| Entidade | Atributos principais | Chave |
|---|---|---|
| `municipio` | nome_municipio, uf | id_municipio (código IBGE) |
| `causa` | origem, tipo, grupo_causa, detalhe_causa | id_causa (substituto) |
| `conjunto_eletrico` | nome_conjunto, total_consumidores | id_conjunto (código ANEEL) |
| `ocorrencia` | inicio_ocorrencia, fim_ocorrencia, tempo_preparacao, tempo_deslocamento, tempo_execucao | id_ocorrencia (substituto) |
| `interrupcao` | consumidores_afetados, inicio_interrupcao, fim_interrupcao | id_interrupcao (substituto) |

Cardinalidades:

- `municipio (1,1) — acontece em — (0,n) ocorrencia`: toda ocorrência tem exatamente 1 município; um município tem 0..n ocorrências.
- `causa (1,1) — tem — (0,n) ocorrencia`: toda ocorrência tem exatamente 1 causa.
- `conjunto_eletrico (1,1) — abrange — (0,n) ocorrencia`: toda ocorrência tem exatamente 1 conjunto elétrico.
- `ocorrencia (0,1) — acarreta — (0,n) interrupcao`: cada interrupção está ligada a 0 ou 1 ocorrência (FK opcional); cada ocorrência gera 0..n interrupções.

### Mapeamento fonte → modelo

| Campo na fonte | Fonte | Vai para |
|---|---|---|
| NumOcorrencia / split_part(NumOrdemInterrupcao,'_',1), composto com o ano de origem | Ocorrências Emerg. / Interrupções | `dados.ocorrencia.num_ocorrencia_origem` |
| DthInicioOcorrenciaAberta | Ocorrências Emergenciais | `dados.ocorrencia.inicio_ocorrencia` |
| DthFimOcorrenciaAberta | Ocorrências Emergenciais | `dados.ocorrencia.fim_ocorrencia` |
| MdaPreparo | Ocorrências Emergenciais | `dados.ocorrencia.tempo_preparacao` |
| MdaDeslocamento | Ocorrências Emergenciais | `dados.ocorrencia.tempo_deslocamento` |
| MdaExecucao | Ocorrências Emergenciais | `dados.ocorrencia.tempo_execucao` |
| CodIBGE (só se cadastrado em `dados.municipio`, senão sentinela) | Ocorrências Emergenciais | `dados.municipio.id_municipio` (⚠️ via join — Interrupções não tem código de município no schema antigo) |
| IdeConjuntoUnidadeConsumidora | Interrupções | `dados.conjunto_eletrico.id_conjunto` |
| DscConjuntoUnidadeConsumidora | Interrupções | `dados.conjunto_eletrico.nome_conjunto` |
| NumConsumidorConjunto | Interrupções | `dados.conjunto_eletrico.total_consumidores` (valor mais recente por conjunto) |
| DscFatoGeradorInterrupcao (1ª parte, separado por " - ") | Interrupções | `dados.causa.origem` |
| DscFatoGeradorInterrupcao (2ª parte) | Interrupções | `dados.causa.tipo` |
| DscFatoGeradorInterrupcao (3ª parte) | Interrupções | `dados.causa.grupo_causa` |
| DscFatoGeradorInterrupcao (4ª parte) | Interrupções | `dados.causa.detalhe_causa` |
| NumOrdemInterrupcao | Interrupções | `dados.interrupcao.num_ordem_interrupcao_origem` (não é único — repete por ocorrência) |
| DatInicioInterrupcao | Interrupções | `dados.interrupcao.inicio_interrupcao` |
| DatFimInterrupcao | Interrupções | `dados.interrupcao.fim_interrupcao` |
| NumUnidadeConsumidora | Interrupções | `dados.interrupcao.consumidores_afetados` |

> Diferente do que o dicionário de dados original indicava, a causa **não** vem pronta em 4 colunas no schema de 2021-2025 — vem em uma única string tipo `"INTERNA - NAO PROGRAMADA - PROPRIAS DO SISTEMA - FALHA DE MATERIAL OU EQUIPAMENTO"`, que o script de transformação staging → dados separa por `" - "`. No schema novo de 2026 já vem em 4 colunas, recombinadas pelo `carregar_staging_aneel.py` no mesmo formato antes de entrar no staging.

## Decisões de modelagem

1. **`total_consumidores` variando no tempo**: usa-se o valor da interrupção mais recente de cada conjunto elétrico (foto do estado atual, não histórico).
2. **Interrupções sem ocorrência correspondente**: *validado em 22/09* — **97,2% das interrupções (todo o período) casam** com uma ocorrência via `split_part(NumOrdemInterrupcao,'_',1) = NumOcorrencia` (+ ano). As restantes **recebem uma ocorrência substituta 1:1** (usando causa/conjunto/horários da própria interrupção), com `id_municipio` apontando para um **município sentinela "não identificado"** (já que não há de onde tirar o município real nesses casos — a única fonte de município é Ocorrências Emergenciais, ligada justamente pela chave que não casou).
3. **Tempos de atendimento** (`inicio_ocorrencia`, `fim_ocorrencia`, `tempo_preparacao`, `tempo_deslocamento`, `tempo_execucao`): vêm da fonte Ocorrências Emergenciais, ligada pela chave de ocorrência.
4. **`nome_municipio`**: não vem em nenhuma das 2 fontes ANEEL (só o código IBGE, e só na fonte Ocorrências Emergenciais); populado a partir da lista de referência dos 185 municípios de PE (`municipios_pe_ibge.csv`). **(22/09)** `cod_ibge` de município fora de PE (ex.: `2511202`, da Paraíba — atendimento perto da divisa) vira o sentinela em vez de tentar gravar direto, já que violaria a FK.
5. **Causa**: fonte trocada de "4 colunas prontas" (suposição inicial, errada) para "1 coluna com 4 níveis separados por ` - `" (`DscFatoGeradorInterrupcao`, fonte real Interrupções, schema 2021-2025) — o parsing entra no script de transformação staging → dados. No schema novo de 2026, a causa já vem em 4 colunas separadas na fonte, recombinadas para o mesmo formato.
6. **`num_ocorrencia_origem` não é único entre anos** *(descoberto em 22/09)*: os códigos da ANEEL são numerados por ano, não globalmente. O valor gravado agora é composto com o ano de origem (`"{codigo}_{ano}"`), tanto para ocorrências reais quanto para as substitutas — sem isso, o `UNIQUE` da coluna quebra ao carregar mais de 1 ano junto.
7. **`staging.interrupcoes` pode acumular linhas duplicadas** *(descoberto em 22/09)*: se alguma carga foi rodada mais de uma vez sem limpar o staging antes, a mesma interrupção (`num_ordem_interrupcao` + ano) pode aparecer repetida. O script de transformação agora remove essas duplicatas logo no início, antes de montar `dados.ocorrencia`/`dados.interrupcao`.

## Extensão INMET (clima)

### Formato do arquivo (verificado em 2021 a 2026)

- 1 CSV por estação dentro do ZIP anual; só entram os arquivos com `_PE_` no nome.
- Separador `;`, codificação latin1, vírgula decimal.
- 8 linhas de cadastro da estação no topo (nome, código, latitude, longitude, altitude, fundação); a tabela começa na linha 9, com 19 colunas iguais em todos os anos.
- Hora sem medição vem com campo vazio (não aparece `-9999`).
- Hora em **UTC** — confirmado pela radiação solar de Recife: pico às 15h UTC = 12h local.

### Tabelas

| Tabela | Grão | Conteúdo |
|---|---|---|
| `staging.inmet_estacao` | estação × ano | cadastro cru do topo do CSV |
| `staging.inmet_horario` | estação × hora (UTC) | as 19 colunas do CSV, sem alteração |
| `dados.estacao` | estação × ano | nome, latitude, longitude, altitude |
| `dados.clima_diario` | estação × dia (hora local) | chuva total, rajada máxima, temperatura máx./mín. e `horas_com_*` |
| `dados.municipio_estacao` | município × ano × ordem | as 3 estações mais próximas e a distância em km |

### Mapeamento fonte → modelo

| Campo no CSV | Vai para |
|---|---|
| CODIGO (WMO) | `dados.estacao.id_estacao` |
| ESTACAO, LATITUDE, LONGITUDE, ALTITUDE | `dados.estacao` |
| Data + Hora UTC, convertidas para UTC-3 | `dados.clima_diario.data_local` |
| PRECIPITAÇÃO TOTAL, HORÁRIO (mm) | `precipitacao_total_mm` (soma do dia) e `horas_com_chuva` |
| VENTO, RAJADA MAXIMA (m/s) | `rajada_max_ms` (máximo do dia) e `horas_com_rajada` |
| TEMPERATURA MÁXIMA / MÍNIMA NA HORA ANT. (AUT) (°C) | `temp_max_c`, `temp_min_c` e `horas_com_temperatura` |
| coordenadas do IBGE (`municipios_pe_coordenadas.csv`) + coordenadas da estação | `dados.municipio_estacao.distancia_km` |

### Decisões

1. **Estação por ano**: o conjunto de estações e as coordenadas mudam de um ano para outro (Recife tem latitude -8,059 em 2021 e -8,019 em 2026; Petrolina não existe em 2026). Por isso `dados.estacao` e `dados.municipio_estacao` têm o ano na chave.
2. **Hora local**: o INMET é convertido de UTC para UTC-3 antes de agrupar por dia. A ANEEL foi tratada como hora local (evidência, não prova: na amostra de 500 ocorrências de 2025, o mínimo fica entre 1h e 4h e o pico às 8h).
3. **Chuva sem medição ≠ chuva zero**: dia sem nenhuma hora medida fica NULL (37% dos dias). As colunas `horas_com_*` dizem quantas horas do dia tiveram medição, por variável.
4. **3 estações mais próximas por município**: a mais próxima muitas vezes não tem dado de chuva no dia; na análise, usa-se a mais próxima que tiver. Distância em linha reta (fórmula de Haversine), do centro do município até a estação.
5. **Sem FK de `dados.municipio_estacao` para `dados.municipio`**, de propósito: o `transformar_staging_dados.py` faz `TRUNCATE ... CASCADE` em `dados.municipio`, e o CASCADE apagaria a ligação com as estações toda vez que a transformação da ANEEL rodasse.
6. **Período**: igual ao da ANEEL, de 01/01/2021 a 30/06/2026 em data local. As 4 estações novas de 2026 (Santa Cruz do Capibaribe, Aliança, Itapissuma e São José da Coroa Grande) só começam em julho/agosto e ficam de fora.

## Estrutura de arquivos

```
SQL/
  01_criar_banco.sql             -- cria o banco bussola_de_crise
  02_criar_tabelas_e_schemas.sql -- cria os schemas staging/dados e as 12 tabelas (7 da ANEEL + 5 do INMET)
Scripts/
  carregar_staging_aneel.py      -- lê os parquet de um ano, filtra Neoenergia PE, carrega no staging
  transformar_staging_dados.py   -- lê o staging completo e popula dados.* (município, causa, conjunto, ocorrência, interrupção)
  carregar_staging_inmet.py      -- lê o ZIP de um ano do INMET, pega só as estações de PE, carrega no staging
  transformar_staging_inmet.py   -- resume por dia (hora local) e liga município <-> 3 estações mais próximas
Dados/
  Bruto/                         -- arquivos originais baixados da ANEEL (parquet), um por ano/fonte -- NÃO vai pro git
  Referencia/
    municipios_pe_ibge.csv       -- lista dos 185 municípios de PE (nome, código IBGE)
    municipios_pe_coordenadas.csv -- latitude/longitude dos 185 municípios de PE (IBGE)
```

## Como rodar

1. **Criar o banco**: conectado ao banco `postgres` (não ao banco novo), rode `SQL/01_criar_banco.sql`.
2. **Criar schemas e tabelas**: troque a conexão para o banco `bussola_de_crise` recém-criado e rode `SQL/02_criar_tabelas_e_schemas.sql` (esse arquivo já cria os schemas `staging` e `dados` antes das tabelas).
3. **Baixar os dados brutos**: para cada ano de 2021 a 2026, baixe o arquivo parquet de Ocorrências Emergenciais e de Interrupções (links na seção "Fontes de dados") e salve em `Dados/Bruto/`.
4. **Carregar o staging**: instale as dependências (`pip install pandas pyarrow sqlalchemy psycopg2-binary`) e rode, uma vez por ano:
   ```
   python Scripts/carregar_staging_aneel.py --ano 2021 --ocorrencias "Dados/Bruto/ocorrencias_2021.parquet" --interrupcoes "Dados/Bruto/interrupcoes_2021.parquet"
   ```
   (repita trocando o ano e os caminhos, para 2022 a 2026)
5. **Transformar staging em dimensões/fatos**:
   ```
   python Scripts/transformar_staging_dados.py --municipios "Dados/Referencia/municipios_pe_ibge.csv"
   ```
   Pode rodar quantas vezes precisar — o script limpa (`TRUNCATE`) as 5 tabelas de `dados.*` no início e repopula do zero a partir de tudo que estiver no staging naquele momento.
6. **INMET — carregar o staging**: baixe o ZIP de cada ano em https://portal.inmet.gov.br/dadoshistoricos, salve em `dados/brutos/` sem extrair e rode, uma vez por ano:
   ```
   python pipeline/carregar_staging_inmet.py --ano 2021 --zip "dados/brutos/2021.zip"
   ```
   Pode rodar de novo o mesmo ano: o script apaga as linhas daquele ano antes de gravar.
7. **INMET — transformar**:
   ```
   python pipeline/transformar_staging_inmet.py --coordenadas "dados/referencia/municipios_pe_coordenadas.csv"
   ```
   Não mexe nas tabelas da ANEEL; pode rodar antes ou depois do `transformar_staging_dados.py`.

## Pendências

- ~~Criar a linha sentinela de município ("não identificado") em `dados.municipio`~~ ✅
- ~~Conferir se as colunas do arquivo de Interrupções são as mesmas em outros anos~~ ✅ (2026 tem schema novo, já tratado)
- ~~Carregar o staging dos demais anos (2022 a 2026)~~ ✅
- ~~Escrever o script de transformação staging → dimensões/fatos~~ ✅ — validado com os 6 anos, ver contagens no topo.
- ~~Planejar o cruzamento com INMET~~ ✅ — extensão INMET carregada (ver seção "Extensão INMET").
- **QA**: confirmar com a base completa que os horários da ANEEL estão em hora local (`SELECT extract(hour FROM inicio_ocorrencia), count(*) FROM dados.ocorrencia GROUP BY 1 ORDER BY 1`).
- **Atenção na análise de clima**: Recife (A301) não tem nenhuma medição de chuva de 2022 a 2025 (100% vazio em 2022-2023 e estação ausente em 2024-2025) — a Região Metropolitana fica com estação mais próxima a ~100 km nesses anos.
- **Atenção na análise de clima**: 44 a 70 municípios (conforme o ano) ficam a mais de 50 km da estação mais próxima; Fernando de Noronha fica a mais de 500 km. Definir um limite de distância antes de cruzar.
