"""
transformar_staging_inmet.py

Lê o que já está carregado em staging.inmet_estacao e staging.inmet_horario
e popula as tabelas de clima do modelo final do banco bussola_de_crise:
  dados.estacao            (1 linha por estação por ano)
  dados.clima_diario       (1 linha por estação por dia, em hora local)
  dados.municipio_estacao  (as 3 estações mais próximas de cada município, por ano)

Regras:
  - O INMET grava em UTC (verificado pela radiação solar de Recife: pico às
    15h UTC = 12h local). Aqui a hora é convertida para UTC-3 antes de
    agrupar por dia, para casar com a data das ocorrências da ANEEL.
  - Período igual ao das fontes ANEEL: 01/01/2021 a 30/06/2026 (data local).
  - Chuva: soma só das horas com medição. Dia sem NENHUMA hora medida fica
    NULL (e não 0) -- "sem medição" é diferente de "não choveu".
  - horas_com_* = quantas horas do dia tiveram medição, por variável.
  - Distância município -> estação: linha reta sobre a Terra (fórmula de
    Haversine), do centro do município (coordenadas do IBGE) até a estação.

-----------------------------------------------------------------------
COMO USAR
-----------------------------------------------------------------------
1) Já deve ter rodado carregar_staging_inmet.py para os anos que quiser.

2) Rode:

   python pipeline/transformar_staging_inmet.py --coordenadas "dados/referencia/municipios_pe_coordenadas.csv"

3) Pede host/porta/banco/usuário/senha do Postgres, igual aos outros.

4) Pode rodar de novo quantas vezes precisar: apaga (TRUNCATE) as 3 tabelas
   de clima no início e repopula a partir de tudo que estiver no staging.
   Não mexe nas tabelas da ANEEL.
-----------------------------------------------------------------------
"""

import argparse
import getpass

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

DATA_INICIO = "2021-01-01"
DATA_FIM = "2026-06-30"
FUSO_HORAS = -3          # Pernambuco: UTC-3, sem horário de verão
ESTACOES_POR_MUNICIPIO = 3
RAIO_TERRA_KM = 6371


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


def limpar_tabelas_clima(engine):
    print("\nLimpando as tabelas de clima (para repopular do zero)...")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE dados.municipio_estacao, dados.clima_diario, dados.estacao"))
    print("  OK.")


def montar_estacao(engine):
    print("\nMontando dados.estacao ...")
    df = pd.read_sql(
        "SELECT cod_estacao, ano_arquivo_origem, nome_estacao, latitude, longitude, altitude "
        "FROM staging.inmet_estacao",
        engine,
    )
    df = df.rename(columns={"cod_estacao": "id_estacao", "ano_arquivo_origem": "ano"})
    df.to_sql("estacao", engine, schema="dados", if_exists="append", index=False)
    print(f"  {len(df):,} linhas (estação x ano) gravadas.")
    return df


def montar_clima_diario(engine):
    print("\nMontando dados.clima_diario ...")
    df = pd.read_sql(
        "SELECT cod_estacao, data_medicao, hora_utc, precipitacao_total_mm, "
        "vento_rajada_max_ms, temp_max_c, temp_min_c "
        "FROM staging.inmet_horario",
        engine,
    )
    print(f"  {len(df):,} linhas horárias lidas do staging.")

    # "0000 UTC" -> 0, "1500 UTC" -> 15
    hora = df["hora_utc"].str[:2].astype(int)
    # data + hora = momento em UTC; somando -3 horas vira hora local
    momento_local = (
        pd.to_datetime(df["data_medicao"])
        + pd.to_timedelta(hora, unit="h")
        + pd.Timedelta(hours=FUSO_HORAS)
    )
    df["data_local"] = momento_local.dt.date

    # corte do período pela data LOCAL
    df = df[(df["data_local"] >= pd.Timestamp(DATA_INICIO).date())
            & (df["data_local"] <= pd.Timestamp(DATA_FIM).date())]

    g = df.groupby(["cod_estacao", "data_local"])
    diario = pd.DataFrame({
        # min_count=1: se nenhuma hora teve medição, a soma fica NULL em vez de 0
        "precipitacao_total_mm": g["precipitacao_total_mm"].sum(min_count=1),
        # count() conta só os valores não vazios = horas com medição
        "horas_com_chuva": g["precipitacao_total_mm"].count(),
        "rajada_max_ms": g["vento_rajada_max_ms"].max(),
        "horas_com_rajada": g["vento_rajada_max_ms"].count(),
        "temp_max_c": g["temp_max_c"].max(),
        "temp_min_c": g["temp_min_c"].min(),
        "horas_com_temperatura": g["temp_max_c"].count(),
    }).reset_index()
    diario = diario.rename(columns={"cod_estacao": "id_estacao"})

    diario.to_sql(
        "clima_diario", engine, schema="dados", if_exists="append",
        index=False, method="multi", chunksize=5000,
    )
    sem_chuva = diario["precipitacao_total_mm"].isna().mean() * 100
    print(f"  {len(diario):,} dias (estação x dia) gravados.")
    print(f"  {sem_chuva:.0f}% dos dias sem nenhuma hora de chuva medida (ficaram NULL).")


def distancia_km(lat1, lon1, lat2, lon2):
    """Fórmula de Haversine: distância em linha reta sobre a superfície da
    Terra entre dois pontos dados em graus de latitude/longitude."""
    # as funções trigonométricas do numpy trabalham em radianos, não em graus
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    # 'a' mede o quanto os dois pontos estão afastados na esfera (de 0 a 1)
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    # transforma em ângulo e multiplica pelo raio da Terra -> quilômetros
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


def montar_municipio_estacao(engine, estacoes, caminho_coordenadas):
    print("\nMontando dados.municipio_estacao ...")
    mun = pd.read_csv(caminho_coordenadas, dtype={"codigo_ibge": str})
    print(f"  {len(mun):,} municípios com coordenadas.")

    # how="cross": combina cada município com cada estação de cada ano
    # (185 municípios x ~13 estações x 6 anos = ~14 mil pares)
    pares = mun.merge(estacoes, how="cross", suffixes=("_mun", "_est"))
    pares["distancia_km"] = distancia_km(
        pares["latitude_mun"], pares["longitude_mun"],
        pares["latitude_est"], pares["longitude_est"],
    ).round(1)

    # numera as estações de cada município/ano da mais perto (1) para a mais longe
    pares = pares.sort_values(["codigo_ibge", "ano", "distancia_km"])
    pares["ordem"] = pares.groupby(["codigo_ibge", "ano"]).cumcount() + 1
    pares = pares[pares["ordem"] <= ESTACOES_POR_MUNICIPIO]

    out = pares.rename(columns={"codigo_ibge": "id_municipio"})[
        ["id_municipio", "ano", "ordem", "id_estacao", "distancia_km"]
    ]
    out.to_sql("municipio_estacao", engine, schema="dados", if_exists="append", index=False)
    print(f"  {len(out):,} ligações gravadas.")

    # resumo: quão longe fica a estação mais próxima
    primeira = out[out["ordem"] == 1]
    print("\n  Distância até a estação mais próxima, por ano (km):")
    resumo = primeira.groupby("ano")["distancia_km"].agg(["median", "max"])
    resumo["municipios_acima_50km"] = primeira[primeira["distancia_km"] > 50].groupby("ano").size()
    print(resumo.fillna(0).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coordenadas", required=True,
        help="CSV com codigo_ibge, nome, latitude, longitude dos municípios de PE",
    )
    args = parser.parse_args()

    engine = pedir_conexao()
    limpar_tabelas_clima(engine)
    estacoes = montar_estacao(engine)
    montar_clima_diario(engine)
    montar_municipio_estacao(engine, estacoes, args.coordenadas)

    print("\nResumo final:")
    with engine.begin() as conn:
        for tabela in ["estacao", "clima_diario", "municipio_estacao"]:
            n = conn.execute(text(f"SELECT COUNT(*) FROM dados.{tabela}")).scalar()
            print(f"  dados.{tabela}: {n:,} linhas")
