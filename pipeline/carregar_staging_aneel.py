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
1) Baixe os 2 arquivos do ano que você quer carregar (ex.: 2026):

   Ocorrências Emergenciais 2026 (parquet):
   https://dadosabertos.aneel.gov.br/dataset/ced06b4c-45a5-4cae-8a7e-f576ffc3b412/resource/d0669ad0-24a2-4f34-85cc-1b08e82d7ad2/download/ocorrencias-emergenciais-rede-distribuicao-2026.parquet

   Interrupções 2026 (parquet):
   https://dadosabertos.aneel.gov.br/dataset/ccb25653-f07b-4f28-84c2-62a89d1f5a56/resource/cf722d0b-aa04-4681-bcd9-8a737e857182/download/interrupcoes-energia-eletrica-2026.parquet

   Salve os dois numa pasta qualquer (ex.: uma pasta "Dados").

2) Instale as dependências (uma vez só), no terminal:
   pip install pandas pyarrow sqlalchemy psycopg2-binary

3) Já deve ter rodado antes os scripts 01_criar_banco.sql e
   02_criar_tabelas_e_schemas.sql (banco bussola_de_crise com os schemas staging
   e dados criados).

4) Rode este script no terminal, apontando para os 2 arquivos baixados:

   python carregar_staging_aneel.py --ano 2026 \
       --ocorrencias "C:/caminho/ocorrencias-emergenciais-rede-distribuicao-2026.parquet" \
       --interrupcoes "C:/caminho/interrupcoes-energia-eletrica-2026.parquet"

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
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Filtro aplicado em NomAgente (contém, sem diferenciar maiúsc./minúsc.).
# Se o filtro pegar agente(s) errado(s) ou nada, ajuste esta string e rode
# de novo -- o script imprime os nomes que bateram para você conferir.
FILTRO_NOM_AGENTE = "PERNAMBUCO"

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

    df_pe = df_pe.rename(columns=COLUNAS_OCORRENCIAS_EMERGENCIAIS)
    df_pe = df_pe[list(COLUNAS_OCORRENCIAS_EMERGENCIAIS.values())]
    df_pe["ano_arquivo_origem"] = ano

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

    # Neste dataset a coluna de nome do agente se chama NomAgenteRegulado
    # (não NomAgente, como no dataset de Ocorrências Emergenciais).
    filtro = df["NomAgenteRegulado"].str.contains(FILTRO_NOM_AGENTE, case=False, na=False)
    df_pe = df.loc[filtro].copy()
    print(f"  {len(df_pe):,} linhas após filtro NomAgenteRegulado contém '{FILTRO_NOM_AGENTE}'")
    print("  Agentes encontrados:", sorted(df_pe["NomAgenteRegulado"].dropna().unique().tolist()))

    df_pe = df_pe.rename(columns=COLUNAS_INTERRUPCOES)
    df_pe = df_pe[list(COLUNAS_INTERRUPCOES.values())]
    df_pe["ano_arquivo_origem"] = ano

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
