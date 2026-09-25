# Bússola de Crise — banco `bussola_de_crise`

Banco de dados que organiza as ocorrências de interrupção de energia da Neoenergia PE (2021-2025 + 1º sem. 2026) e os dados climáticos do INMET no mesmo período, para dar suporte às perguntas analíticas do projeto.

Documentação completa (modelo de dados, decisões, achados de QA): [`docs/modelagem_banco.md`](docs/modelagem_banco.md).

## 1. Dados coletados

| Fonte | Origem | Coletado em | Volume |
|---|---|---|---|
| ANEEL — Ocorrências Emergenciais | https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao | 21/09/2026 | 2.049.989 linhas (Neoenergia PE, 2021-2026) |
| ANEEL — Interrupções de Energia Elétrica | https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao | 22/09/2026 | 1.288.322 linhas (Neoenergia PE, 2021-2026) |
| INMET — Dados históricos | https://portal.inmet.gov.br/dadoshistoricos | 24/09/2026 | 604.584 linhas (13 estações de PE, 2021-2026) |

Os arquivos brutos (`.parquet` da ANEEL e `.zip` do INMET) **não ficam versionados neste repositório** — são grandes demais para o Git. Baixe direto das fontes acima (os links exatos, por ano, estão nos comentários no topo de `pipeline/carregar_staging_aneel.py`) e salve localmente, fora do controle de versão.

**Dicionário de dados mínimo**: a tabela "Mapeamento fonte → modelo" em [`docs/modelagem_banco.md`](docs/modelagem_banco.md) lista, para cada coluna relevante do arquivo de origem, o que ela significa e para qual coluna do banco ela vai — tanto para a ANEEL quanto para o INMET (seção "Extensão INMET").

## 2. Banco modelado

- Schema versionado em [`sql/01_criar_banco.sql`](sql/01_criar_banco.sql) (cria o banco) e [`sql/02_criar_tabelas_e_schemas.sql`](sql/02_criar_tabelas_e_schemas.sql) (cria os schemas `staging`/`dados` e as 12 tabelas: 7 da ANEEL + 5 do INMET).
- Modelo relacional com FKs entre as tabelas (`dados.ocorrencia` → `dados.municipio`/`causa`/`conjunto_eletrico`; `dados.interrupcao` → `dados.ocorrencia`; `dados.municipio_estacao` → `dados.estacao`).
- Dados carregados e consultáveis — ver seção "Contagens finais validadas" na documentação completa.

## 3. Pipeline

### Dependências

```
pip install -r requirements.txt
```

### Como rodar do zero

1. Criar o banco: conectado ao banco `postgres`, rode `sql/01_criar_banco.sql`.
2. Criar schemas e tabelas: troque a conexão para `bussola_de_crise` e rode `sql/02_criar_tabelas_e_schemas.sql`.
3. Baixar os dados brutos da ANEEL (links no topo de `pipeline/carregar_staging_aneel.py`) e do INMET (https://portal.inmet.gov.br/dadoshistoricos), salvando localmente (fora do git).
4. Carregar o staging da ANEEL, um ano de cada vez (2021 a 2026):
   ```
   python pipeline/carregar_staging_aneel.py --ano 2021 --ocorrencias "<caminho>/ocorrencias_2021.parquet" --interrupcoes "<caminho>/interrupcoes_2021.parquet"
   ```
5. Transformar a ANEEL (staging → dimensões/fatos):
   ```
   python pipeline/transformar_staging_dados.py --municipios "dados/referencia/municipios_pe_ibge.csv"
   ```
6. Carregar o staging do INMET, um ano de cada vez (2021 a 2026):
   ```
   python pipeline/carregar_staging_inmet.py --ano 2021 --zip "<caminho>/2021.zip"
   ```
7. Transformar o INMET:
   ```
   python pipeline/transformar_staging_inmet.py --coordenadas "dados/referencia/municipios_pe_coordenadas.csv"
   ```

Os scripts de carga (passos 4 e 6) são idempotentes — rodar o mesmo ano de novo apaga a carga anterior antes de gravar, sem duplicar. Os scripts de transformação (passos 5 e 7) recriam as tabelas finais do zero a cada execução e podem ser rodados em qualquer ordem entre si.

## 4. Perguntas do canvas

Consultas e análises individuais de cada pergunta ficam em `sql/` e `analises/`. Ver `docs/modelagem_banco.md` para o detalhe de quais perguntas já foram validadas com dados reais.
