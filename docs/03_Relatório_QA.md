# Relatório de QA — Reteste (#1, #2, #5) + Integração INMET (#3) + Achado #6

**Data:** 25/09/2026
**Ambiente testado:** banco local, recorte completo (2021–2025 + 1º semestre de 2026)
**Escopo:** reteste dos achados do 1º e 2º relatórios após correções da analista, e validação da nova integração com dados do INMET (clima)

---------------------------------------------------------------------------------------

## 1. Resumo executivo

Depois das correções dos analistas, foram retestados os achados #1 (duplicação em `dados.interrupcao`), #2 (documentação da coluna causa) e #5 (bugs do schema novo de 2026). **#1 e #2 seguem corrigidos e confirmados; do achado #5, 2 dos 3 problemas foram corrigidos (5a e 5c), mas o 5b (tempos de preparo/deslocamento/execução em 2026) segue com bug.** Além disso, a integração com o INMET (que fechava o achado #3, dados de clima ausentes) foi implementada e testada com sucesso, com 2 limitações de dados documentadas (não são bugs) e 1 achado novo, menor (#6).

---------------------------------------------------------------------------------------


## 2. Achado #1 — Duplicação em `dados.interrupcao` (RECONFIRMADO CORRIGIDO, escala completa)

Reteste final com 2021–2026 completos (recorte total do projeto): `dados.interrupcao` = **1.199.657 linhas**. Conferência: soma das cargas de staging de todos os anos = 1.288.322 interrupções; após remover 88.665 duplicatas reais (mesmo `num_ordem_interrupcao` + `ano_arquivo_origem`), sobram **1.199.657** — número que bate exatamente com o final gravado. Taxa de casamento: 93,1% (consistente com os 92,7%-92,9% observados nos testes anteriores, em escalas menores). **Nenhum sinal de duplicação em escala completa — achado fechado com confiança alta.**

---------------------------------------------------------------------------------------


## 3. Achado #2 — Documentação da coluna causa (RECONFIRMADO FECHADO)

Sem mudanças desde o fechamento anterior: `staging.interrupcoes` tem só 1 coluna de causa (`dsc_fato_gerador_interrupcao`), dividida em 3 ou 4 níveis conforme o caso. `dados.causa` grava `detalhe_causa = NULL` apenas nos 2 casos esperados (nível 3 e a linha sentinela). Nenhuma regressão encontrada.

---------------------------------------------------------------------------------------


## 4. Achado #5 — Schema novo de 2026 (PARCIALMENTE CORRIGIDO)

| Sub-achado | Status | Evidência do reteste |
|---|---|---|
| 5a — datas nulas em `staging.interrupcoes` | ✅ Corrigido | `dat_inicio_interrupcao` 100% preenchido (178.448/178.448) |
| 5b — tempos de etapa nulos em `staging.ocorrencias_emergenciais` | ❌ **Ainda com bug** | `mda_preparo` continua 100% `NULL` (0 de 205.210) |
| 5c — filtro de 30/06 incorreto | ✅ Corrigido | Data máxima agora é exatamente `2026-06-30 23:54:00`, dentro do limite. O próprio script passou a avisar quando remove linhas fora do período (`"25.701 linhas... após 30/06/2026 removidas"`) |

**Bônus encontrado no reteste:** o `carregar_staging_aneel.py` passou a apagar sozinho as linhas de um ano antes de recarregá-lo (*"204.149 linhas de 2026 já existentes... foram apagadas antes desta carga"*), o que parece corrigir também o **achado #4** (não-idempotência). A confirmar se esse comportamento vale para todos os anos, não só 2026.

**Recomendação:** revisar o mapeamento das colunas `mda_preparo`, `mda_deslocamento` e `mda_execucao` no schema novo de 2026 — ainda bloqueia a pergunta 4 do canvas (duração por etapa) especificamente para esse ano.

---------------------------------------------------------------------------------------


## 5. Integração com o INMET (fecha o achado #3)

A analista enviou os scripts `carregar_staging_inmet.py` e `transformar_staging_inmet.py`, que resolvem a lacuna do achado #3 (dados de clima ausentes, necessários para a pergunta 5 do canvas).

### Validação (todos os anos, 2021–2026)

| Tabela | Linhas | Checagem |
|---|---|---|
| `dados.estacao` | 75 | 13+13+13+12+12+12 estações por ano — bate |
| `dados.clima_diario` | 25.180 | Próximo do esperado (estações × dias) |
| `dados.municipio_estacao` | 3.330 | 185 municípios × 3 estações × 6 anos — bate exato |

### Limitações de dados documentadas (não são bugs)

1. **Fernando de Noronha**: nenhuma estação do INMET na ilha; a mais próxima fica entre 547 km e 640 km. Estimativas de clima para esse município não são confiáveis.
2. **Estação A301 (Recife) ausente em 2024 e 2025**: confirmado que o arquivo da estação simplesmente não veio no ZIP do INMET nesses 2 anos (não é falha do script — o arquivo não existe na fonte). Isso é visível na tabela de distâncias: a mediana de distância município→estação sobe de 33,7 km (2021-2023) para 41,9 km (2024-2025), e os municípios acima de 50 km sobem de 44 para 70 — efeito direto da perda de Recife como referência nesses anos. Volta ao normal em 2026.

---------------------------------------------------------------------------------------


## 6. Achado #6 (novo, menor) — Filtro de 2026 no INMET

Assim como a ANEEL tinha um desvio no filtro de 30/06 (achado #5c, já corrigido), o `carregar_staging_inmet.py` também carrega 2026 até **01/07/2026**, 1 dia além do previsto — bem menor que o desvio que a ANEEL tinha (que ia até 31/07), mas ainda inconsistente com o recorte oficial do projeto.

**Sugestão:** ajustar o filtro para excluir também esse último dia.

---------------------------------------------------------------------------------------


## 7. Próximos passos

- Confirmar os números finais do achado #1 com 2021–2026 completos (rodada de hoje).
- Cobrar correção do achado #5b (tempos de etapa em 2026).
- Cobrar correção do achado #6 (filtro do INMET em 2026).
- Confirmar se a autolimpeza por ano do `carregar_staging_aneel.py` (achado #4) vale para todos os anos, não só 2026.
