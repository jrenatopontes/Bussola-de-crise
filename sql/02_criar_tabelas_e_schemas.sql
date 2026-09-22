-- =====================================================================
-- Bússola de Crise — Neoenergia PE — bussola_de_crise
-- Tabelas do schema "dados", seguindo o diagrama de modelagem do projeto
-- (5 entidades: municipio, causa, conjunto_eletrico, ocorrencia, interrupcao)
--
-- Fontes de dados (3, confirmadas no chat em 22/09):
--   1. ANEEL — "Ocorrências Emergenciais nas Redes de Distribuição"
--      https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao
--      -> único lugar com inicio/fim de OCORRÊNCIA e os tempos de
--         preparo/deslocamento/execução.
--   2. ANEEL — "Interrupções de Energia Elétrica nas Redes de Distribuição"
--      https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao
--      -> município, causa (já em 4 colunas), conjunto elétrico
--         (nome + total de consumidores) e consumidores afetados.
--   3. INMET — Dados históricos (https://portal.inmet.gov.br/dadoshistoricos)
--      -> clima; join externo por município/data, fora deste schema
--         (não há entidade de clima no diagrama enviado).
--
-- As duas fontes ANEEL são ligadas por ocorrência: NumOcorrencia (fonte 1)
-- = primeira parte de NumOrdemInterrupcao, ANTES do "_" (fonte 2) --
-- NumOrdemInterrupcao vem no formato "{num_ocorrencia}_{id_interrupcao}".
-- VALIDADO com dados reais da Neoenergia PE em 2021: split_part(x,'_',1)
-- bate com num_ocorrencia em 92,7% das interrupções (178.618 de 192.644).
-- Não existe CodOcorrencia/CodInterrupcao na fonte 2 real -- essa
-- suposição inicial (baseada num dicionário de dados desatualizado)
-- estava errada, e a primeira validação (chave igual sem split) também
-- estava errada -- era coincidência de outra distribuidora.
--
-- Arquivos anuais das 2 fontes ANEEL: 2021 a 2025 completos + 2026
-- filtrado até 30/06 (período ampliado no canvas do projeto).
-- =====================================================================
-- Rode conectado ao banco bussola_de_crise, depois de 01_criar_banco.sql
--   psql -U postgres -h localhost -d bussola_de_crise -f 02_criar_tabelas_e_schemas.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- SCHEMAS: criados aqui (não no 01_criar_banco.sql) porque
-- precisam rodar já conectado ao banco bussola_de_crise.
-- ---------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS staging;   -- espelho bruto dos arquivos de origem
CREATE SCHEMA IF NOT EXISTS dados;     -- modelo dimensional

-- ---------------------------------------------------------------------
-- STAGING 1: espelho bruto dos arquivos ANEEL de OCORRÊNCIAS EMERGENCIAIS
-- (mesmo layout usado no banco de 2025 anterior; 15 colunas originais).
-- Fonte de inicio/fim de ocorrência e dos tempos de atendimento.
-- ---------------------------------------------------------------------
CREATE TABLE staging.ocorrencias_emergenciais (
    ano_arquivo_origem            smallint,     -- controle nosso: 2021..2026 (2026 = só 1º semestre)
    dat_geracao_conjunto_dados     date,
    nom_agente                     text,
    num_cpf_cnpj                   text,
    num_ocorrencia                  text,       -- chave de ligação com staging.interrupcoes.num_ordem_interrupcao
    ide_conj_und_consumidoras      text,
    dth_inicio_ocorrencia_aberta    timestamp,
    dsc_canal_atendimento           text,
    dth_fim_ocorrencia_aberta       timestamp,
    dsc_ocorrencia_aberta           text,
    dsc_num_interrupcao             text,       -- observado igual a num_ocorrencia na amostra real; mantido para auditoria
    mda_preparo                     numeric,
    mda_deslocamento                numeric,
    mda_execucao                    numeric,
    num_veiculo                     text,
    cod_ibge                        text
);

CREATE INDEX ix_staging_oe_num_ocorrencia   ON staging.ocorrencias_emergenciais (num_ocorrencia);
CREATE INDEX ix_staging_oe_num_interrupcao  ON staging.ocorrencias_emergenciais (dsc_num_interrupcao);
CREATE INDEX ix_staging_oe_ano              ON staging.ocorrencias_emergenciais (ano_arquivo_origem);

-- ---------------------------------------------------------------------
-- STAGING 2: espelho bruto dos arquivos ANEEL de INTERRUPÇÕES.
-- ATUALIZADO em 22/09 com as colunas REAIS do arquivo de 2021 (18 colunas)
-- -- o dicionário oficial usado antes estava desatualizado/errado: não
-- existe CodMunicipioIBGE, CodOcorrencia/CodInterrupcao nem causa em 4
-- colunas separadas nesta fonte.
--
-- O que esta fonte REALMENTE traz nativamente (sem precisar de join):
--   conjunto elétrico (ide/dsc_conjunto_unidade_consumidora, num_consumidor_conjunto)
--   causa em 1 coluna só, com 4 níveis separados por " - " (dsc_fato_gerador_interrupcao)
--   datas de início/fim da interrupção, nível de tensão, nº de UCs atingidas
-- O que esta fonte NÃO traz (precisa vir de staging.ocorrencias_emergenciais,
-- via join num_ordem_interrupcao = num_ocorrencia): o MUNICÍPIO (só existe
-- cod_ibge no dataset de Ocorrências Emergenciais).
-- ---------------------------------------------------------------------
CREATE TABLE staging.interrupcoes (
    ano_arquivo_origem                smallint,     -- controle nosso: 2021..2026 (2026 = só 1º semestre)
    dat_geracao_conjunto_dados        date,
    ide_conjunto_unidade_consumidora  text,
    dsc_conjunto_unidade_consumidora  text,
    dsc_alimentador_subestacao        text,
    dsc_subestacao_distribuicao       text,
    num_ordem_interrupcao             text,       -- formato "{num_ocorrencia}_{id_interrupcao}"; split_part(..., '_', 1) = staging.ocorrencias_emergenciais.num_ocorrencia (92,7% de casamento, validado com dados reais de 2021)
    dsc_tipo_interrupcao              text,
    ide_motivo_interrupcao            text,
    dat_inicio_interrupcao            timestamp,
    dat_fim_interrupcao               timestamp,
    dsc_fato_gerador_interrupcao      text,       -- causa em 1 string, 4 níveis separados por " - "
    num_nivel_tensao                  numeric,
    num_unidade_consumidora           integer,    -- nº de UCs atingidas nesta interrupção (varia linha a linha)
    num_consumidor_conjunto           integer,    -- total de consumidores do conjunto (constante por conjunto)
    num_ano                           smallint,
    nom_agente_regulado               text,
    sig_agente                        text,
    num_cpf_cnpj                      text
);

CREATE INDEX ix_staging_int_num_ordem_interrupcao ON staging.interrupcoes (num_ordem_interrupcao);
CREATE INDEX ix_staging_int_conjunto              ON staging.interrupcoes (ide_conjunto_unidade_consumidora);
CREATE INDEX ix_staging_int_ano                   ON staging.interrupcoes (ano_arquivo_origem);

-- ---------------------------------------------------------------------
-- DIMENSÃO: municipio
-- municipio (1,1) --- acontece_em --- (0,n) ocorrencia
--   => cada ocorrência tem exatamente 1 município (FK obrigatória)
--   => cada município tem 0..n ocorrências
-- id_municipio como TEXT (código IBGE).
-- ATUALIZADO 22/09: o dataset Interrupções NÃO tem código de município.
-- O único lugar com o código IBGE é CodIBGE, na fonte Ocorrências
-- Emergenciais -- ou seja, município só chega em dados.ocorrencia através
-- do join com staging.ocorrencias_emergenciais (num_ordem_interrupcao =
-- num_ocorrencia). PENDÊNCIA: validar com os dados reais que % das linhas
-- de interrupção conseguem casar com uma linha de ocorrência emergencial
-- -- as que não casarem ficam sem município garantido.
-- ---------------------------------------------------------------------
CREATE TABLE dados.municipio (
    id_municipio    text PRIMARY KEY,   -- CodIBGE (fonte: Ocorrências Emergenciais, via join)
    nome_municipio  text,               -- não vem em nenhuma das 2 fontes ANEEL; via referência externa (ver observações)
    uf              char(2)
);

-- ---------------------------------------------------------------------
-- DIMENSÃO: conjunto_eletrico
-- conjunto_eletrico (1,1) --- abrange --- (0,n) ocorrencia
-- id_conjunto como TEXT: IdeConjuntoUnidadeConsumidora, presente em toda
-- linha de Interrupções (não depende do join com Ocorrências Emergenciais).
-- ---------------------------------------------------------------------
CREATE TABLE dados.conjunto_eletrico (
    id_conjunto          text PRIMARY KEY,   -- IdeConjuntoUnidadeConsumidora (fonte: Interrupções)
    nome_conjunto        text,               -- DscConjuntoUnidadeConsumidora (fonte: Interrupções)
    total_consumidores   integer             -- NumConsumidorConjunto (fonte: Interrupções; varia no tempo — ver observações)
);

-- ---------------------------------------------------------------------
-- DIMENSÃO: causa
-- causa (1,1) --- tem --- (0,n) ocorrencia
-- ATUALIZADO 22/09: a fonte Interrupções NÃO traz causa em 4 colunas
-- separadas -- traz 1 única coluna (DscFatoGeradorInterrupcao) com os 4
-- níveis concatenados por " - ", ex.:
--   "INTERNA - NAO PROGRAMADA - PROPRIAS DO SISTEMA - FALHA DE MATERIAL OU EQUIPAMENTO"
-- O script de transformação staging -> dados (ainda a escrever) precisa
-- fazer o split por " - " em até 4 partes:
--   origem        <- parte 1
--   tipo          <- parte 2
--   grupo_causa   <- parte 3
--   detalhe_causa <- parte 4
-- Presente em toda linha de Interrupções (não depende do join).
-- id_causa continua sendo substituto (surrogate), pois a fonte não traz
-- um código de causa, só a descrição.
-- ---------------------------------------------------------------------
CREATE TABLE dados.causa (
    id_causa       serial PRIMARY KEY,
    origem         text,
    tipo           text,
    grupo_causa    text,
    detalhe_causa  text,
    CONSTRAINT uq_causa UNIQUE (origem, tipo, grupo_causa, detalhe_causa)
);

-- ---------------------------------------------------------------------
-- FATO: ocorrencia (grão = 1 ocorrência)
-- ATUALIZADO 22/09: a chave de ligação real entre as 2 fontes ANEEL é
-- NumOcorrencia (Ocorrências Emergenciais) = split_part(NumOrdemInterrupcao,
-- '_', 1) (Interrupções) -- validado com dados reais de 2021 da Neoenergia
-- PE: 92,7% de casamento (178.618 de 192.644 interrupções). As ~7,3% sem
-- ocorrência correspondente recebem uma ocorrência substituta 1:1 com
-- município "não identificado" (não há de onde tirar o município real
-- para esses casos).
-- inicio/fim/tempos vêm da fonte Ocorrências Emergenciais.
-- município vem da fonte Ocorrências Emergenciais (CodIBGE) -- ver
-- observação na tabela dados.municipio. causa e conjunto_eletrico vêm da
-- fonte Interrupções (presentes em toda linha, não dependem do join).
-- ---------------------------------------------------------------------
CREATE TABLE dados.ocorrencia (
    id_ocorrencia          bigserial PRIMARY KEY,
    num_ocorrencia_origem  text UNIQUE,   -- NumOcorrencia (Ocorrências Emerg.) = NumOrdemInterrupcao (Interrupções)
    id_municipio           text NOT NULL REFERENCES dados.municipio (id_municipio),
    id_causa               integer NOT NULL REFERENCES dados.causa (id_causa),
    id_conjunto            text NOT NULL REFERENCES dados.conjunto_eletrico (id_conjunto),
    inicio_ocorrencia      timestamp,   -- DthInicioOcorrenciaAberta (fonte: Ocorrências Emergenciais)
    fim_ocorrencia         timestamp,   -- DthFimOcorrenciaAberta (fonte: Ocorrências Emergenciais)
    tempo_preparacao       numeric,     -- MdaPreparo (fonte: Ocorrências Emergenciais)
    tempo_deslocamento     numeric,     -- MdaDeslocamento (fonte: Ocorrências Emergenciais)
    tempo_execucao         numeric      -- MdaExecucao (fonte: Ocorrências Emergenciais)
);

CREATE INDEX ix_ocorrencia_municipio ON dados.ocorrencia (id_municipio);
CREATE INDEX ix_ocorrencia_causa     ON dados.ocorrencia (id_causa);
CREATE INDEX ix_ocorrencia_conjunto  ON dados.ocorrencia (id_conjunto);

-- ---------------------------------------------------------------------
-- FATO: interrupcao (grão = 1 interrupção)
-- ocorrencia (0,1) --- acarreta --- (0,n) interrupcao
--   => cada interrupção está ligada a 0 ou 1 ocorrência (FK opcional)
--   => cada ocorrência gera 0..n interrupções
-- ATUALIZADO 22/09: NumOrdemInterrupcao vem no formato
-- "{num_ocorrencia}_{id_interrupcao}" -- a parte antes do "_" é a chave da
-- ocorrência (repetida em toda interrupção que pertence a ela; é
-- exatamente o padrão 1 ocorrência -> N interrupções do diagrama), a parte
-- depois do "_" identifica a interrupção em si. Por isso a coluna abaixo
-- (que guarda o valor completo, para auditoria) NÃO é UNIQUE -- ela serve
-- só de referência; o id_ocorrencia é resolvido via split_part(...,'_',1).
-- ---------------------------------------------------------------------
CREATE TABLE dados.interrupcao (
    id_interrupcao                bigserial PRIMARY KEY,
    num_ordem_interrupcao_origem  text,          -- NumOrdemInterrupcao (fonte: Interrupções) = num_ocorrencia_origem
    id_ocorrencia                 bigint REFERENCES dados.ocorrencia (id_ocorrencia),
    consumidores_afetados         integer,       -- NumUnidadeConsumidora (fonte: Interrupções)
    inicio_interrupcao            timestamp,     -- DatInicioInterrupcao (fonte: Interrupções)
    fim_interrupcao               timestamp      -- DatFimInterrupcao (fonte: Interrupções)
);

CREATE INDEX ix_interrupcao_ocorrencia         ON dados.interrupcao (id_ocorrencia);
CREATE INDEX ix_interrupcao_num_ordem_origem   ON dados.interrupcao (num_ordem_interrupcao_origem);
