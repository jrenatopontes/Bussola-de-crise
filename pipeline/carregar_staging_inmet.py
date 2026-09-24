"""
carregar_staging_inmet.py

Carrega, para UM ano, os dados horários das estações automáticas do INMET
em Pernambuco nas tabelas de staging do banco bussola_de_crise:
  staging.inmet_estacao  (cadastro: nome, coordenadas, 1 linha por estação)
  staging.inmet_horario  (medições de hora em hora, as 19 colunas do CSV)

Mesmo papel do carregar_staging_aneel.py, só que para a fonte INMET. O
passo seguinte (resumir por dia e ligar município <-> estação) é o
transformar_staging_inmet.py.

-----------------------------------------------------------------------
COMO USAR 
-----------------------------------------------------------------------
1) Baixe o ZIP do ano em https://portal.inmet.gov.br/dadoshistoricos e
   salve em dados/brutos/ SEM EXTRAIR (pasta ignorada pelo Git). O script
   lê só os arquivos de PE direto de dentro do ZIP.
     ex.: dados/brutos/2021.zip

2) Já deve ter rodado 01_criar_banco.sql e 02_criar_tabelas_e_schemas.sql.

3) Rode no terminal (exemplo para 2021 -- repita para 2022 a 2026):

   python pipeline/carregar_staging_inmet.py --ano 2021 --zip "dados/brutos/2021.zip"

4) Ele pede host/porta/banco/usuário/senha do Postgres, igual ao script
   da ANEEL.

5) Pode rodar de novo o mesmo ano sem medo: antes de gravar, ele apaga
   do staging as linhas daquele ano (não duplica).
-----------------------------------------------------------------------

Formato do arquivo (verificado em 2021 e 2026):
  - 1 CSV por estação, nome tipo INMET_NE_PE_A301_RECIFE_01-01-2021_A_31-12-2021.CSV
  - separador ";", codificação latin1, vírgula decimal
  - 8 linhas de cadastro da estação no topo, tabela a partir da linha 9
  - hora sem medição = campo vazio
  - cada linha termina com ";" sobrando (vira uma coluna vazia, descartada)
"""

import argparse
import getpass
import zipfile

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Mesmo fim de período das fontes ANEEL (2026 = só 1º semestre). O INMET
# está em UTC: 30/06 às 21h em Recife já é 01/07 em UTC, por isso o
# corte aqui é 01/07. O corte exato por data local é feito na
# transformação.
DATA_LIMITE_UTC = "2026-07-01"

# As 19 colunas do CSV, na ordem em que aparecem, e o nome no staging.
# Nomes copiados do cabeçalho real (2021 e 2026 são iguais).
COLUNAS_INMET = {
    "Data": "data_medicao",
    "Hora UTC": "hora_utc",
    "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)": "precipitacao_total_mm",
    "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)": "pressao_estacao_mb",
    "PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB)": "pressao_max_mb",
    "PRESSÃO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB)": "pressao_min_mb",
    "RADIACAO GLOBAL (Kj/m²)": "radiacao_global_kj_m2",
    "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)": "temp_bulbo_seco_c",
    "TEMPERATURA DO PONTO DE ORVALHO (°C)": "temp_orvalho_c",
    "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)": "temp_max_c",
    "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)": "temp_min_c",
    "TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (°C)": "temp_orvalho_max_c",
    "TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C)": "temp_orvalho_min_c",
    "UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)": "umidade_max_pct",
    "UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)": "umidade_min_pct",
    "UMIDADE RELATIVA DO AR, HORARIA (%)": "umidade_rel_pct",
    "VENTO, DIREÇÃO HORARIA (gr) (° (gr))": "vento_direcao_graus",
    "VENTO, RAJADA MAXIMA (m/s)": "vento_rajada_max_ms",
    "VENTO, VELOCIDADE HORARIA (m/s)": "vento_velocidade_ms",
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


def numero_br(valor):
    """Converte texto com vírgula decimal ("-8,0591") em número (-8.0591)."""
    return float(valor.replace(",", "."))


def ler_cadastro(zf, nome_arquivo):
    """Lê as 8 linhas do topo do CSV (cadastro da estação)."""
    with zf.open(nome_arquivo) as f:
        linhas = [f.readline().decode("latin1").strip() for _ in range(8)]
    # cada linha é "CHAVE:;valor" -> vira um dicionário {CHAVE: valor}
    cadastro = {}
    for linha in linhas:
        chave, valor = linha.split(";", 1)
        cadastro[chave.rstrip(":")] = valor
    return {
        "cod_estacao": cadastro["CODIGO (WMO)"],
        "nome_estacao": cadastro["ESTACAO"],
        "uf": cadastro["UF"],
        "latitude": numero_br(cadastro["LATITUDE"]),
        "longitude": numero_br(cadastro["LONGITUDE"]),
        "altitude": numero_br(cadastro["ALTITUDE"]),
        "data_fundacao": cadastro["DATA DE FUNDACAO"],
    }


def ler_medicoes(zf, nome_arquivo):
    """Lê a tabela de medições horárias (da linha 9 em diante)."""
    with zf.open(nome_arquivo) as f:
        df = pd.read_csv(f, sep=";", encoding="latin1", skiprows=8, decimal=",")

    # o ";" sobrando no fim de cada linha vira uma coluna "Unnamed: 19" vazia
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Confere se o cabeçalho é exatamente o esperado. Se o INMET mudar o
    # layout num ano, o script para aqui em vez de gravar coluna trocada.
    if list(df.columns) != list(COLUNAS_INMET.keys()):
        raise SystemExit(
            f"\nERRO: cabeçalho diferente do esperado em {nome_arquivo}\n"
            f"Colunas encontradas: {list(df.columns)}\n"
            "Me avise com esse print para ajustar o COLUNAS_INMET."
        )

    df = df.rename(columns=COLUNAS_INMET)
    df["data_medicao"] = pd.to_datetime(df["data_medicao"], format="%Y/%m/%d")
    return df


def apagar_ano(engine, ano):
    """Idempotência: se o ano já foi carregado antes, apaga para não duplicar."""
    with engine.begin() as conn:
        for tabela in ("inmet_horario", "inmet_estacao"):
            n = conn.execute(
                text(f"DELETE FROM staging.{tabela} WHERE ano_arquivo_origem = :ano"),
                {"ano": ano},
            ).rowcount
            if n:
                print(f"  {n:,} linhas antigas de {ano} apagadas de staging.{tabela}")


def carregar_inmet(engine, ano, caminho_zip):
    print(f"\nAbrindo {caminho_zip} ...")
    zf = zipfile.ZipFile(caminho_zip)
    arquivos_pe = sorted(n for n in zf.namelist() if "_PE_" in n)
    print(f"  {len(zf.namelist())} arquivos no ZIP, {len(arquivos_pe)} de PE")

    estacoes = []
    medicoes = []
    for nome in arquivos_pe:
        cadastro = ler_cadastro(zf, nome)
        df = ler_medicoes(zf, nome)
        df = df[df["data_medicao"] <= DATA_LIMITE_UTC]

        if df.empty:
            # estação que só começou depois do fim do período (ex.: Aliança,
            # que começa em 02/08/2026) -- não entra
            print(f"  {cadastro['cod_estacao']} {cadastro['nome_estacao']}: sem dados no período, ignorada")
            continue

        df.insert(0, "cod_estacao", cadastro["cod_estacao"])
        df.insert(0, "ano_arquivo_origem", ano)
        medicoes.append(df)

        cadastro["ano_arquivo_origem"] = ano
        estacoes.append(cadastro)

        chuva_vazia = 100 * df["precipitacao_total_mm"].isna().mean()
        print(
            f"  {cadastro['cod_estacao']} {cadastro['nome_estacao']:<28} "
            f"{len(df):>6,} horas | chuva sem medição: {chuva_vazia:3.0f}%"
        )

    df_estacao = pd.DataFrame(estacoes)
    df_horario = pd.concat(medicoes, ignore_index=True)

    apagar_ano(engine, ano)

    print("\n  Gravando em staging.inmet_estacao ...")
    df_estacao.to_sql("inmet_estacao", engine, schema="staging", if_exists="append", index=False)

    print("  Gravando em staging.inmet_horario ...")
    df_horario.to_sql(
        "inmet_horario",
        engine,
        schema="staging",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )
    return df_estacao, df_horario


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, required=True, help="Ano do arquivo (ex.: 2021)")
    parser.add_argument("--zip", required=True, help="Caminho do ZIP do INMET (ex.: dados/brutos/2021.zip)")
    args = parser.parse_args()

    engine = pedir_conexao()
    df_estacao, df_horario = carregar_inmet(engine, args.ano, args.zip)

    print("\nResumo da carga de staging do INMET para o ano", args.ano)
    print(f"  staging.inmet_estacao: {len(df_estacao):,} estações")
    print(f"  staging.inmet_horario: {len(df_horario):,} linhas")
