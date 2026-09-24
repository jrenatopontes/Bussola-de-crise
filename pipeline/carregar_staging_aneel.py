"""
carregar_staging_aneel.py

Baixa (você baixa manualmente) e carrega, para UM ano, os dois arquivos da
ANEEL (Ocorrências Emergenciais + Interrupções) nas tabelas de staging do
banco bussola_de_crise, já filtrando pela Neoenergia PE.

Este script só carrega o "staging" (espelho bruto). O passo seguinte —
transformar staging em dimensões/fatos (dados.municipio, dados.causa,
dados.ocorrencia, dados.interrupcao) — é um script separado, que a gente
escreve depois de conferir que essa primeira carga saiu como esperado.

-----------------------------------------------------------------------
COMO USAR (passo a passo)
-----------------------------------------------------------------------
1) Baixe os 2 arquivos do ano que você quer carregar. Os arquivos brutos
   NÃO ficam versionados neste repositório (são grandes demais para o
   Git) -- baixe direto da ANEEL, um ano de cada vez, e salve em
   dados/brutos/ (pasta ignorada pelo Git de propósito).

   ANEEL -- Ocorrências Emergenciais nas Redes de Distribuição
   (página do dataset: https://dadosabertos.aneel.gov.br/dataset/ocorrencias-emergenciais-nas-redes-de-distribuicao)
     2021: https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/bca75c34-e3c7-4db2-a518-b76e6e18979c/download/ocorrencias-emergenciais-rede-distribuicao-2021.parquet
     2022: https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/25b24e8e-544d-42b9-9a8f-3e61f6a6eab1/download/ocorrencias-emergenciais-rede-distribuicao-2022.parquet
     2023: https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/560b6a3d-39b5-4b38-94ef-ca73d745866f/download/ocorrencias-emergenciais-rede-distribuicao-2023.parquet
     2024: https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/ef1d1ae6-39f1-4d9c-ace8-3c5024ca777a/download/ocorrencias-emergenciais-rede-distribuicao-2024.parquet
     2025: https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/6adda6b2-2e24-4637-8689-f48787847e8b/download/ocorrencias-emergenciais-rede-distribuicao-2025.parquet
     2026: https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/d0669ad0-24a2-4f34-85cc-1b08e82d7ad2/download/ocorrencias-emergenciais-rede-distribuicao-2026.parquet

   ANEEL -- Interrupções de Energia Elétrica nas Redes de Distribuição
   (página do dataset: https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao)
     2021: https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/011e0086-8b2f-4fbc-a32b-f7c0f7bc9957/download/interrupcoes-energia-eletrica-2021.parquet
     2022: https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/f40b948c-81a3-4d56-8e35-0af9c2533178/download/interrupcoes-energia-eletrica-2022.parquet
     2023: https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/ddc26540-cd8c-4eef-a1ad-a234d24ed9c4/download/interrupcoes-energia-eletrica-2023.parquet
     2024: https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/fc5ca52c-329c-4443-a2d6-08ccec711ade/download/interrupcoes-energia-eletrica-2024.parquet
     2025: https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/691de320-cb3d-471b-b9ec-8c1b86af8c83/download/interrupcoes-energia-eletrica-2025.parquet
     2026: https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/cf722d0b-aa04-4681-bcd9-8a737e857182/download/interrupcoes-energia-eletrica-2026.parquet

2) Instale as dependências (uma vez só), no terminal:
   pip install pandas pyarrow sqlalchemy psycopg2-binary

3) Já deve ter rodado antes os scripts 01_criar_banco.sql e
   02_criar_tabelas_e_schemas.sql (banco bussola_de_crise com os schemas staging
   e dados criados).

4) Rode este script no terminal, apontando para os 2 arquivos baixados
   (exemplo para 2026 -- repita trocando o ano e os nomes dos arquivos
   para 2021, 2022, 2023, 2024 e 2025):

   python carregar_staging_aneel.py --ano 2026 \
       --ocorrencias "dados/brutos/ocorrencias-emergenciais-rede-distribuicao-2026.parquet" \
       --interrupcoes "dados/brutos/interrupcoes-energia-eletrica-2026.parquet"

   (ajuste os caminhos para onde você salvou os arquivos)

5) Ele vai pedir host/porta/banco/usuário/senha do Postgres (aperte Enter
   para aceitar os valores padrão entre colchetes, exceto a senha).

6) No fim, ele imprime quantas linhas entraram em cada tabela de staging
   e a lista de nomes de agente que bateram no filtro — confira se só
   aparece a Neoenergia PE (Celpe) e mais nada.
-----------------------------------------------------------------------
"""

import argparse
import getpass

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Filtro aplicado em NomAgente (contém, sem diferenciar maiúsc./minúsc.).
# Se o filtro pegar agente(s) errado(s) ou nada, ajuste esta string e rode
# de novo -- o script imprime os nomes que bateram para você conferir.
FILTRO_NOM_AGENTE = "PERNAMBUCO"

# Achado #5c do QA (24/09): o recorte do projeto é "1º semestre de 2026",
# mas o arquivo de 2026 baixado da ANEEL vem com dados até 31/07 -- não
# existe corte automático no arquivo em si, então filtramos explicitamente
# por data para o ano de 2026 (só ele; os demais anos não têm esse recorte).
ANO_COM_CORTE_SEMESTRAL = 2026
CORTE_SEMESTRAL = pd.Timestamp("2026-06-30 23:59:59")

COLUNAS_OCORRENCIAS_EMERGENCIAIS = {
    "DatGeracaoConjuntoDados": "dat_geracao_conjunto_dados",
    "NomAgente": "nom_agente",
    "NumCPFCNPJ": "num_cpf_cnpj",
    "NumOcorrencia": "num_ocorrencia",
    "IdeConjUndConsumidoras": "ide_conj_und_consumidoras",
    "DthInicioOcorrenciaAberta": "dth_inicio_ocorrencia_aberta",
    "DscCanalAtendimento": "dsc_canal_atendimento",
    "DthFimOcorrenciaAberta": "dth_fim_ocorrencia_aberta",
    "DscOcorrenciaAberta": "dsc_ocorrencia_aberta",
    "DscNumInterrupcao": "dsc_num_interrupcao",
    "MdaPreparo": "mda_preparo",
    "MdaDeslocamento": "mda_deslocamento",
    "MdaExecucao": "mda_execucao",
    "NumVeiculo": "num_veiculo",
    "CodIBGE": "cod_ibge",
}

# Schema alternativo, visto pela 1a vez no arquivo de 2026 -- a ANEEL
# reformulou o dataset de Ocorrências Emergenciais nesse ano: causa já vem
# em 4 colunas separadas (igual ao dataset de Interrupções) e vários campos
# foram renomeados/removidos (não existe mais NumVeiculo, por exemplo).
#
# Achado #5b do QA (24/09), INVESTIGADO E FECHADO (não é bug do pipeline):
# mda_preparo, mda_deslocamento e mda_execucao vêm 100% NULL para 2026.
# Conferido em 24/09 contra o arquivo real: os nomes abaixo
# (NumTempoPreparacao/NumTempoDeslocamento/NumTempoExecucao) ESTÃO corretos
# -- essas colunas existem no arquivo com esses nomes exatos. O problema é
# que a ANEEL publica essas 3 colunas vazias ("") para 100% das linhas de
# 2026 -- provavelmente porque só são preenchidas quando o atendimento é
# finalizado do lado deles, e os dados de 2026 (ano corrente) ainda não
# tiveram tempo de "fechar", diferente de 2021-2025. Ou seja: limitação da
# fonte para este ano específico, não algo que o script possa corrigir.
# Impacto: a pergunta 4 do canvas (duração média por etapa) fica sem dado
# disponível para 2026 -- os outros 5 anos não são afetados.
COLUNAS_OCORRENCIAS_EMERGENCIAIS_SCHEMA_NOVO = {
    "DatGeracaoConjuntoDados": "dat_geracao_conjunto_dados",
    "NomAgente": "nom_agente",
    "NumCnpjDistribuidora": "num_cpf_cnpj",
    "CodOcorrenciaEmergencial": "num_ocorrencia",
    "CodConjUnidConsumidora": "ide_conj_und_consumidoras",
    "DthIniOcorrencia": "dth_inicio_ocorrencia_aberta",
    "DscFormaConhecimento": "dsc_canal_atendimento",
    "DthFimOcorrencia": "dth_fim_ocorrencia_aberta",
    "DscInterrupcaoAssociada": "dsc_num_interrupcao",
    "NumTempoPreparacao": "mda_preparo",
    "NumTempoDeslocamento": "mda_deslocamento",
    "NumTempoExecucao": "mda_execucao",
    "CodMunicipioIBGE": "cod_ibge",
}

# ATUALIZADO em 22/09 a partir das colunas REAIS do arquivo de 2021 (o
# dicionário oficial da ANEEL que eu tinha usado antes não bate com o
# arquivo real -- este dataset não tem CodMunicipioIBGE, CodOcorrencia nem
# as 4 colunas separadas de causa). Chave de ligação real com
# staging.ocorrencias_emergenciais: NumOrdemInterrupcao = NumOcorrencia.
COLUNAS_INTERRUPCOES = {
    "DatGeracaoConjuntoDados": "dat_geracao_conjunto_dados",
    "IdeConjuntoUnidadeConsumidora": "ide_conjunto_unidade_consumidora",
    "DscConjuntoUnidadeConsumidora": "dsc_conjunto_unidade_consumidora",
    "DscAlimentadorSubestacao": "dsc_alimentador_subestacao",
    "DscSubestacaoDistribuicao": "dsc_subestacao_distribuicao",
    "NumOrdemInterrupcao": "num_ordem_interrupcao",
    "DscTipoInterrupcao": "dsc_tipo_interrupcao",
    "IdeMotivoInterrupcao": "ide_motivo_interrupcao",
    "DatInicioInterrupcao": "dat_inicio_interrupcao",
    "DatFimInterrupcao": "dat_fim_interrupcao",
    "DscFatoGeradorInterrupcao": "dsc_fato_gerador_interrupcao",
    "NumNivelTensao": "num_nivel_tensao",
    "NumUnidadeConsumidora": "num_unidade_consumidora",
    "NumConsumidorConjunto": "num_consumidor_conjunto",
    "NumAno": "num_ano",
    "NomAgenteRegulado": "nom_agente_regulado",
    "SigAgente": "sig_agente",
    "NumCPFCNPJ": "num_cpf_cnpj",
}

# Schema alternativo, visto pela 1a vez no arquivo de 2026 -- mesma
# reformulação da ANEEL que já vimos em Ocorrências Emergenciais. Diferenças
# principais: (1) agora existem CodOcorrencia e CodInterrupcao como colunas
# separadas -- reconstruímos num_ordem_interrupcao no formato antigo
# "{num_ocorrencia}_{id_interrupcao}" para não quebrar a lógica de join
# (split_part(...,'_',1)) nem o script de transformação; (2) a causa vem em
# 4 colunas separadas (DscFatoGeradorOrigem/Tipo/Causa/Detalhe) em vez de 1
# string só -- reconstruímos dsc_fato_gerador_interrupcao concatenando com
# " - " para manter o mesmo formato que dados.causa espera; (3) o filtro de
# agente usa NomAgente, não NomAgenteRegulado (que não existe nesse schema).
# Campos sem equivalente direto (dsc_alimentador_subestacao,
# dsc_subestacao_distribuicao, dsc_tipo_interrupcao, ide_motivo_interrupcao)
# ficam NULL para 2026 -- nenhum deles é usado no modelo dados.* final
# (são só informativos no staging).
COLUNAS_INTERRUPCOES_SCHEMA_NOVO = {
    "DatGeracaoConjuntoDados": "dat_geracao_conjunto_dados",
    "CodConjUnidadeConsumidora": "ide_conjunto_unidade_consumidora",
    "DscConjuntoUnidadeConsumidora": "dsc_conjunto_unidade_consumidora",
    "NumNivelTensao": "num_nivel_tensao",
    "QtdConsumidoresAfetados": "num_unidade_consumidora",
    "QtdConsumidoresAtivos": "num_consumidor_conjunto",
    "AnoCompetencia": "num_ano",
    "NomAgente": "nom_agente_regulado",
    "SigAgente": "sig_agente",
    "NumCNPJDistribuidora": "num_cpf_cnpj",
    # Achado #5a do QA (24/09): estas 2 colunas existem no schema novo (com
    # o MESMO nome do schema antigo -- ver "Colunas reais de Interrupções
    # (schema novo, 2026)" na documentação), mas faltavam neste dicionário.
    # Sem elas, dat_inicio_interrupcao/dat_fim_interrupcao ficavam 100% NULL
    # para 2026 (o fallback "coluna não existe -> None" do código abaixo
    # entrava em ação silenciosamente).
    "DatInicioInterrupcao": "dat_inicio_interrupcao",
    "DatFimInterrupcao": "dat_fim_interrupcao",
}


def limpar_staging_do_ano(engine, tabela, ano):
    """Apaga (se existirem) as linhas já carregadas desse ano nessa tabela de
    staging antes de inserir de novo -- torna o script seguro de rodar mais
    de uma vez para o mesmo ano (idempotente). Sem isso (visto na prática ao
    recarregar 2026 depois de corrigir os achados #5a/#5c do QA em 24/09), a
    carga antiga (com bug) fica duplicada ao lado da carga nova (corrigida)."""
    with engine.begin() as conn:
        resultado = conn.execute(
            text(f"DELETE FROM staging.{tabela} WHERE ano_arquivo_origem = :ano"),
            {"ano": ano},
        )
        if resultado.rowcount:
            print(
                f"  Atenção: {resultado.rowcount:,} linhas de {ano} já existentes em "
                f"staging.{tabela} foram apagadas antes desta carga (evita duplicar "
                "se você já tinha carregado esse ano antes)."
            )


def pedir_conexao():
    host = input("Host do PostgreSQL [localhost]: ").strip() or "localhost"
    port = input("Porta [5432]: ").strip() or "5432"
    dbname = input("Banco [bussola_de_crise]: ").strip() or "bussola_de_crise"
    user = input("Usuário [postgres]: ").strip() or "postgres"
    password = getpass.getpass("Senha: ")
    url = URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=dbname,
    )
    return create_engine(url)


def carregar_ocorrencias_emergenciais(engine, ano, caminho):
    print(f"\nLendo {caminho} ...")
    df = pd.read_parquet(caminho)
    print(f"  {len(df):,} linhas no Brasil todo")

    filtro = df["NomAgente"].str.contains(FILTRO_NOM_AGENTE, case=False, na=False)
    df_pe = df.loc[filtro].copy()
    print(f"  {len(df_pe):,} linhas após filtro NomAgente contém '{FILTRO_NOM_AGENTE}'")
    print("  Agentes encontrados:", sorted(df_pe["NomAgente"].dropna().unique().tolist()))

    colunas_finais = list(COLUNAS_OCORRENCIAS_EMERGENCIAIS.values())

    if "CodOcorrenciaEmergencial" in df_pe.columns:
        # Schema novo (visto pela 1a vez no arquivo de 2026): causa já vem
        # em 4 colunas separadas -- reconstrói dsc_ocorrencia_aberta no
        # mesmo formato dos anos anteriores (só para manter consistência no
        # staging; a transformação para dados.* já lê a causa direto de
        # staging.interrupcoes, não usa esta coluna).
        print("  Schema novo detectado (formato visto em 2026) -- usando mapeamento alternativo.")
        df_pe = df_pe.rename(columns=COLUNAS_OCORRENCIAS_EMERGENCIAIS_SCHEMA_NOVO)
        df_pe["dsc_ocorrencia_aberta"] = (
            df_pe.get("DscFatoGeradorOrigem", pd.Series(dtype="object")).fillna("")
            + ";" + df_pe.get("DscFatoGeradorTipo", pd.Series(dtype="object")).fillna("")
            + ";" + df_pe.get("DscFatoGeradorCausa", pd.Series(dtype="object")).fillna("")
            + ";" + df_pe.get("DscFatoGeradorDetalhe", pd.Series(dtype="object")).fillna("")
        )
        df_pe["num_veiculo"] = None  # não existe nesse schema
        for col in colunas_finais:
            if col not in df_pe.columns:
                df_pe[col] = None
        df_pe = df_pe[colunas_finais]
    else:
        df_pe = df_pe.rename(columns=COLUNAS_OCORRENCIAS_EMERGENCIAIS)
        df_pe = df_pe[colunas_finais]

    # As colunas de tempo (mda_preparo/deslocamento/execucao) são NUMERIC no
    # Postgres. Em alguns anos (visto em 2026) essas colunas chegam do
    # parquet como string vazia "" em vez de NULL/NaN quando o tempo não
    # foi registrado -- Postgres rejeita "" num campo numeric ("invalid
    # input syntax for type numeric"). pd.to_numeric com errors="coerce"
    # converte "" (e qualquer outro valor não numérico) para NaN, que o
    # to_sql grava corretamente como NULL.
    for col in ("mda_preparo", "mda_deslocamento", "mda_execucao"):
        df_pe[col] = pd.to_numeric(df_pe[col], errors="coerce")

    # Achado #5c do QA (24/09): o arquivo de 2026 vem com dados até 31/07,
    # um mês além do recorte do projeto ("1º semestre de 2026"). Filtra por
    # dth_inicio_ocorrencia_aberta para manter só até 30/06.
    if ano == ANO_COM_CORTE_SEMESTRAL:
        antes = len(df_pe)
        df_pe = df_pe[
            pd.to_datetime(df_pe["dth_inicio_ocorrencia_aberta"]) <= CORTE_SEMESTRAL
        ]
        if len(df_pe) < antes:
            print(
                f"  Atenção: {antes - len(df_pe):,} linhas com dth_inicio_ocorrencia_aberta "
                f"após 30/06/{ano} removidas (projeto cobre só o 1º semestre)."
            )

    df_pe["ano_arquivo_origem"] = ano

    limpar_staging_do_ano(engine, "ocorrencias_emergenciais", ano)

    print("  Gravando em staging.ocorrencias_emergenciais ...")
    df_pe.to_sql(
        "ocorrencias_emergenciais",
        engine,
        schema="staging",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )
    print(f"  OK: {len(df_pe):,} linhas gravadas.")
    return df_pe


def carregar_interrupcoes(engine, ano, caminho):
    print(f"\nLendo {caminho} ...")
    df = pd.read_parquet(caminho)
    print(f"  {len(df):,} linhas no Brasil todo")

    # Schema novo (visto pela 1a vez em 2026): tem CodInterrupcao/CodOcorrencia
    # como colunas separadas e usa NomAgente (não NomAgenteRegulado, que não
    # existe nesse schema) para o nome do agente.
    schema_novo = "CodInterrupcao" in df.columns
    coluna_filtro = "NomAgente" if schema_novo else "NomAgenteRegulado"

    filtro = df[coluna_filtro].str.contains(FILTRO_NOM_AGENTE, case=False, na=False)
    df_pe = df.loc[filtro].copy()
    print(f"  {len(df_pe):,} linhas após filtro {coluna_filtro} contém '{FILTRO_NOM_AGENTE}'")
    print("  Agentes encontrados:", sorted(df_pe[coluna_filtro].dropna().unique().tolist()))

    colunas_finais = list(COLUNAS_INTERRUPCOES.values())

    if schema_novo:
        print("  Schema novo detectado (formato visto em 2026) -- usando mapeamento alternativo.")
        # Reconstrói num_ordem_interrupcao no formato antigo
        # "{num_ocorrencia}_{id_interrupcao}" a partir das colunas separadas,
        # para não quebrar a lógica de join (split_part(...,'_',1)).
        df_pe["num_ordem_interrupcao"] = (
            df_pe["CodOcorrencia"].astype(str) + "_" + df_pe["CodInterrupcao"].astype(str)
        )
        # Reconstrói dsc_fato_gerador_interrupcao (1 string, 4 níveis
        # separados por " - ") a partir das 4 colunas separadas desse schema.
        df_pe["dsc_fato_gerador_interrupcao"] = (
            df_pe.get("DscFatoGeradorOrigem", pd.Series(dtype="object")).fillna("")
            + " - " + df_pe.get("DscFatoGeradorTipo", pd.Series(dtype="object")).fillna("")
            + " - " + df_pe.get("DscFatoGeradorCausa", pd.Series(dtype="object")).fillna("")
            + " - " + df_pe.get("DscFatoGeradorDetalhe", pd.Series(dtype="object")).fillna("")
        )
        df_pe = df_pe.rename(columns=COLUNAS_INTERRUPCOES_SCHEMA_NOVO)
        # Campos sem equivalente nesse schema (não usados no modelo dados.*
        # final, só informativos no staging) ficam NULL para 2026.
        for col in ("dsc_alimentador_subestacao", "dsc_subestacao_distribuicao",
                    "dsc_tipo_interrupcao", "ide_motivo_interrupcao"):
            df_pe[col] = None
        for col in colunas_finais:
            if col not in df_pe.columns:
                df_pe[col] = None
        df_pe = df_pe[colunas_finais]
    else:
        df_pe = df_pe.rename(columns=COLUNAS_INTERRUPCOES)
        df_pe = df_pe[colunas_finais]

    # Achado #5c do QA (24/09): mesmo recorte de 30/06 aplicado em
    # staging.ocorrencias_emergenciais, agora também em staging.interrupcoes
    # (só foi possível confirmar aqui depois de corrigir o achado #5a --
    # antes, dat_inicio_interrupcao vinha 100% NULL para 2026).
    if ano == ANO_COM_CORTE_SEMESTRAL:
        antes = len(df_pe)
        df_pe = df_pe[
            pd.to_datetime(df_pe["dat_inicio_interrupcao"]) <= CORTE_SEMESTRAL
        ]
        if len(df_pe) < antes:
            print(
                f"  Atenção: {antes - len(df_pe):,} linhas com dat_inicio_interrupcao "
                f"após 30/06/{ano} removidas (projeto cobre só o 1º semestre)."
            )

    df_pe["ano_arquivo_origem"] = ano

    # Mesma cautela do fix de ocorrências: campos numeric/integer no Postgres
    # podem chegar como string vazia em vez de NULL. Coerce evita o mesmo
    # "invalid input syntax for type numeric/integer" que já vimos.
    for col in ("num_nivel_tensao", "num_unidade_consumidora", "num_consumidor_conjunto", "num_ano"):
        df_pe[col] = pd.to_numeric(df_pe[col], errors="coerce")

    limpar_staging_do_ano(engine, "interrupcoes", ano)

    print("  Gravando em staging.interrupcoes ...")
    df_pe.to_sql(
        "interrupcoes",
        engine,
        schema="staging",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )
    print(f"  OK: {len(df_pe):,} linhas gravadas.")
    return df_pe


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, required=True, help="Ano dos arquivos (ex.: 2026)")
    parser.add_argument("--ocorrencias", required=True, help="Caminho do parquet de Ocorrências Emergenciais")
    parser.add_argument("--interrupcoes", required=True, help="Caminho do parquet de Interrupções")
    args = parser.parse_args()

    engine = pedir_conexao()

    df_oe = carregar_ocorrencias_emergenciais(engine, args.ano, args.ocorrencias)
    df_int = carregar_interrupcoes(engine, args.ano, args.interrupcoes)

    print("\nResumo da carga de staging para o ano", args.ano)
    print(f"  staging.ocorrencias_emergenciais: {len(df_oe):,} linhas")
    print(f"  staging.interrupcoes:             {len(df_int):,} linhas")
    print("\nConfira os nomes de agente impressos acima -- se vier algo além")
    print("da Neoenergia PE, ajuste FILTRO_NOM_AGENTE no topo do script e rode de novo.")
