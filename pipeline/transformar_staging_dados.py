"""
transformar_staging_dados.py

Lê o que já está carregado nas tabelas de staging (staging.ocorrencias_emergenciais
e staging.interrupcoes) e popula o modelo final do banco bussola_de_crise:
dados.municipio, dados.causa, dados.conjunto_eletrico, dados.ocorrencia e
dados.interrupcao.

Aplica as regras de modelagem validadas com os dados reais de 2021:
  - Chave de ligação entre as 2 fontes ANEEL: NumOcorrencia (Ocorrências
    Emergenciais) = primeira parte de NumOrdemInterrupcao, ANTES do "_"
    (Interrupções). Casamento real observado: 92,7%.
  - Interrupções sem ocorrência correspondente (os outros ~7,3%) viram uma
    ocorrência substituta 1:1, com município "não identificado" (não há de
    onde tirar o município real nesses casos).
  - Causa: DscFatoGeradorInterrupcao (1 coluna) dividida em até 4 níveis por
    " - " (origem, tipo, grupo_causa, detalhe_causa).
  - Conjunto elétrico: total_consumidores usa o valor da interrupção mais
    recente de cada conjunto (foto do estado atual).
  - nome_municipio: vem do arquivo de referência dos 185 municípios de PE
    (não vem em nenhuma das 2 fontes ANEEL).
  - Um mesmo num_ocorrencia pode ter mais de 1 chamado em
    staging.ocorrencias_emergenciais (achado do QA em 23/09); mantemos só o
    chamado mais antigo por (num_ocorrencia, ano) antes de ligar com
    staging.interrupcoes, para não duplicar linhas de dados.interrupcao.

-----------------------------------------------------------------------
COMO USAR
-----------------------------------------------------------------------
1) Já deve ter rodado carregar_staging_aneel.py para todos os anos que você
   quer no modelo final (pode ser só 2021, ou 2021 a 2026 -- este script
   sempre usa TUDO que já estiver no staging no momento em que rodar).

2) Rode (ajuste o caminho do CSV de referência se for diferente):

   python transformar_staging_dados.py --municipios "dados/referencia/municipios_pe_ibge.csv"

3) Vai pedir host/porta/banco/usuário/senha do Postgres, igual ao
   carregar_staging_aneel.py.

4) Este script é seguro de rodar de novo quantas vezes precisar: ele
   APAGA (TRUNCATE) as 5 tabelas de dados.* no início e repopula do zero a
   partir do staging -- então, se você carregar mais anos no staging depois,
   é só rodar este script de novo para atualizar o modelo final.
-----------------------------------------------------------------------
"""

import argparse
import getpass
import traceback

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

MUNICIPIO_NAO_IDENTIFICADO = "0000000"
CONJUNTO_NAO_IDENTIFICADO = "0000000"


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


def limpar_tabelas_dados(engine):
    print("\nLimpando as tabelas dados.* (para repopular do zero)...")
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE dados.interrupcao, dados.ocorrencia, "
                "dados.causa, dados.conjunto_eletrico, dados.municipio "
                "RESTART IDENTITY CASCADE"
            )
        )
    print("  OK.")


def carregar_referencia_municipios(caminho):
    """Lê o CSV de referência dos municípios de PE. Detecta separador
    (vírgula ou tab) e nomes das colunas de forma flexível (não sabemos o
    formato exato de antemão)."""
    print(f"\nLendo referência de municípios: {caminho} ...")
    # sep=None + engine="python" detecta sozinho se o arquivo é separado por
    # vírgula, ponto e vírgula ou tab (visto na prática: o arquivo real do
    # repositório do projeto usa tab, com só 2 colunas -- Municipio e
    # Codigo_IBGE, sem coluna de UF).
    ref = pd.read_csv(caminho, dtype=str, sep=None, engine="python")
    ref.columns = [c.strip().lower() for c in ref.columns]

    def achar_coluna(candidatos, obrigatoria=True):
        for c in candidatos:
            if c in ref.columns:
                return c
        if obrigatoria:
            raise SystemExit(
                f"\nERRO: não encontrei nenhuma destas colunas no CSV de referência: {candidatos}\n"
                f"Colunas encontradas no arquivo: {list(ref.columns)}\n"
                "Me avise com esse print para eu ajustar o script."
            )
        return None

    col_ibge = achar_coluna(["codigo_ibge", "cod_ibge", "codigoibge", "ibge", "codigo"])
    col_nome = achar_coluna(["nome_municipio", "municipio", "nome"])
    # UF é opcional: o CSV real do projeto não tem essa coluna (é só a lista
    # dos municípios de PE, então UF é sempre "PE" para todas as linhas).
    col_uf = achar_coluna(["uf", "estado"], obrigatoria=False)

    if col_uf:
        ref = ref[[col_ibge, col_nome, col_uf]].rename(
            columns={col_ibge: "id_municipio", col_nome: "nome_municipio", col_uf: "uf"}
        )
    else:
        ref = ref[[col_ibge, col_nome]].rename(
            columns={col_ibge: "id_municipio", col_nome: "nome_municipio"}
        )
        ref["uf"] = "PE"

    ref["id_municipio"] = ref["id_municipio"].str.strip()
    ref = ref.drop_duplicates(subset="id_municipio")
    print(f"  {len(ref):,} municípios de referência.")
    return ref


def montar_municipio(engine, ref_municipios):
    print("\nMontando dados.municipio ...")
    out = ref_municipios.copy()
    # registro sentinela para interrupções sem ocorrência correspondente
    sentinela = pd.DataFrame(
        [{"id_municipio": MUNICIPIO_NAO_IDENTIFICADO, "nome_municipio": "Não identificado", "uf": None}]
    )
    out = pd.concat([out, sentinela], ignore_index=True)
    out.to_sql("municipio", engine, schema="dados", if_exists="append", index=False, method="multi", chunksize=5000)
    print(f"  {len(out):,} municípios gravados (incluindo o sentinela).")


def montar_causa(engine):
    print("\nMontando dados.causa ...")
    df = pd.read_sql(
        "SELECT DISTINCT dsc_fato_gerador_interrupcao FROM staging.interrupcoes "
        "WHERE dsc_fato_gerador_interrupcao IS NOT NULL",
        engine,
    )
    partes = df["dsc_fato_gerador_interrupcao"].str.split(" - ", expand=True)
    partes = partes.reindex(columns=range(4))
    partes.columns = ["origem", "tipo", "grupo_causa", "detalhe_causa"]
    for col in partes.columns:
        partes[col] = partes[col].str.strip()
    partes = partes.drop_duplicates()

    # causa sentinela, para as poucas linhas sem descrição de causa
    sentinela = pd.DataFrame(
        [{"origem": "NAO IDENTIFICADA", "tipo": None, "grupo_causa": None, "detalhe_causa": None}]
    )
    partes = pd.concat([partes, sentinela], ignore_index=True)

    partes.to_sql("causa", engine, schema="dados", if_exists="append", index=False, method="multi", chunksize=5000)
    print(f"  {len(partes):,} causas distintas gravadas (incluindo a sentinela).")


def montar_conjunto_eletrico(engine):
    print("\nMontando dados.conjunto_eletrico ...")
    df = pd.read_sql(
        "SELECT ide_conjunto_unidade_consumidora, dsc_conjunto_unidade_consumidora, "
        "num_consumidor_conjunto, dat_inicio_interrupcao "
        "FROM staging.interrupcoes WHERE ide_conjunto_unidade_consumidora IS NOT NULL",
        engine,
    )
    df = df.sort_values("dat_inicio_interrupcao").drop_duplicates(
        subset="ide_conjunto_unidade_consumidora", keep="last"
    )
    out = df.rename(
        columns={
            "ide_conjunto_unidade_consumidora": "id_conjunto",
            "dsc_conjunto_unidade_consumidora": "nome_conjunto",
            "num_consumidor_conjunto": "total_consumidores",
        }
    )[["id_conjunto", "nome_conjunto", "total_consumidores"]]

    sentinela = pd.DataFrame(
        [{"id_conjunto": CONJUNTO_NAO_IDENTIFICADO, "nome_conjunto": "Não identificado", "total_consumidores": None}]
    )
    out = pd.concat([out, sentinela], ignore_index=True)

    out.to_sql("conjunto_eletrico", engine, schema="dados", if_exists="append", index=False, method="multi", chunksize=5000)
    print(f"  {len(out):,} conjuntos elétricos gravados (incluindo o sentinela).")


def montar_ocorrencia_e_interrupcao(engine):
    print("\nLendo staging.interrupcoes e staging.ocorrencias_emergenciais ...")
    interr = pd.read_sql("SELECT * FROM staging.interrupcoes", engine)
    oe = pd.read_sql("SELECT * FROM staging.ocorrencias_emergenciais", engine)
    print(f"  {len(interr):,} linhas de interrupções, {len(oe):,} linhas de ocorrências emergenciais.")

    # staging.interrupcoes pode ter linhas duplicadas (mesma interrupção +
    # ano repetida) se alguma carga foi rodada mais de uma vez sem limpar o
    # staging antes -- sem isso, o num_ordem_interrupcao duplicado quebra o
    # UNIQUE de dados.ocorrencia.num_ocorrencia_origem lá na frente.
    antes = len(interr)
    interr = interr.drop_duplicates(subset=["num_ordem_interrupcao", "ano_arquivo_origem"])
    if len(interr) < antes:
        print(
            f"  Atenção: {antes - len(interr):,} linhas duplicadas em staging.interrupcoes "
            "removidas (mesmo num_ordem_interrupcao + ano_arquivo_origem)."
        )

    # ids de município já cadastrados em dados.municipio (os 185 de PE + o
    # sentinela). cod_ibge da fonte às vezes traz município de outro estado
    # (ex.: atendimento perto da divisa) -- qualquer código fora desse
    # conjunto precisa virar o sentinela, senão viola a FK de dados.ocorrencia.
    municipios_validos = set(
        pd.read_sql("SELECT id_municipio FROM dados.municipio", engine)["id_municipio"]
    )

    # chave de ligação: parte antes do "_" em num_ordem_interrupcao
    interr["occ_key"] = interr["num_ordem_interrupcao"].str.split("_").str[0]

    # causa: split em 4 níveis (igual ao montar_causa, para conseguir religar depois)
    causa_partes = interr["dsc_fato_gerador_interrupcao"].str.split(" - ", expand=True)
    causa_partes = causa_partes.reindex(columns=range(4))
    causa_partes.columns = ["origem", "tipo", "grupo_causa", "detalhe_causa"]
    for col in causa_partes.columns:
        causa_partes[col] = causa_partes[col].str.strip()
    interr = pd.concat([interr, causa_partes], axis=1)

    causa_ids = pd.read_sql("SELECT id_causa, origem, tipo, grupo_causa, detalhe_causa FROM dados.causa", engine)
    interr = interr.merge(causa_ids, how="left", on=["origem", "tipo", "grupo_causa", "detalhe_causa"])
    sentinela_causa_id = causa_ids.loc[causa_ids["origem"] == "NAO IDENTIFICADA", "id_causa"].iloc[0]
    interr["id_causa"] = interr["id_causa"].fillna(sentinela_causa_id).astype(int)

    # conjunto: usa direto o id (já é a mesma chave da tabela dados.conjunto_eletrico)
    interr["id_conjunto"] = interr["ide_conjunto_unidade_consumidora"].fillna(CONJUNTO_NAO_IDENTIFICADO)

    # staging.ocorrencias_emergenciais pode ter MAIS DE 1 chamado apontando
    # para o mesmo num_ocorrencia (regra de negócio: vários clientes na
    # mesma localização podem gerar chamados separados para a mesma
    # ocorrência). Achado do QA em 23/09: sem tratar isso, o merge abaixo
    # vira um produto cartesiano -- cada interrupção que casa com um
    # num_ocorrencia de múltiplos chamados era gravada 1 vez POR CHAMADO,
    # inflando dados.interrupcao (345.621 gravadas vs. 177.986 esperadas,
    # em 2021). Colapsamos para 1 chamado por (num_ocorrencia, ano) antes
    # do merge -- critério de desempate: o mais antigo por data/hora de
    # abertura (dth_inicio_ocorrencia_aberta).
    antes_oe = len(oe)
    oe = oe.sort_values("dth_inicio_ocorrencia_aberta").drop_duplicates(
        subset=["num_ocorrencia", "ano_arquivo_origem"], keep="first"
    )
    if len(oe) < antes_oe:
        print(
            f"  Atenção: {antes_oe - len(oe):,} chamados extras em staging.ocorrencias_emergenciais "
            "(mesmo num_ocorrencia + ano) colapsados em 1 só (o mais antigo por data/hora de abertura)."
        )

    # liga com ocorrencias_emergenciais por occ_key + ano
    oe_slim = oe[[
        "num_ocorrencia", "ano_arquivo_origem", "cod_ibge",
        "dth_inicio_ocorrencia_aberta", "dth_fim_ocorrencia_aberta",
        "mda_preparo", "mda_deslocamento", "mda_execucao",
    ]].rename(columns={"num_ocorrencia": "occ_key"})

    interr = interr.merge(oe_slim, how="left", on=["occ_key", "ano_arquivo_origem"], indicator=True)
    casadas = interr["_merge"] == "both"
    print(f"  {casadas.sum():,} de {len(interr):,} interrupções casaram com uma ocorrência ({100 * casadas.mean():.1f}%).")

    # -------------------------------------------------------------
    # dados.ocorrencia -- 1 linha por occ_key/ano quando casou; 1 linha por
    # interrupção (1:1) quando não casou.
    # -------------------------------------------------------------
    matched = interr[casadas].copy()
    # 1 representante por (occ_key, ano) -- causa/conjunto/tempos deveriam ser
    # os mesmos para todas as interrupções da mesma ocorrência; pegamos a primeira.
    ocorrencia_matched = (
        matched.sort_values(["occ_key", "ano_arquivo_origem"])
        .drop_duplicates(subset=["occ_key", "ano_arquivo_origem"], keep="first")
        .assign(
            # occ_key sozinho não é único entre anos (a numeração da ANEEL é
            # por ano) -- compõe com o ano de origem para garantir o UNIQUE
            # de dados.ocorrencia.num_ocorrencia_origem.
            num_ocorrencia_origem=lambda d: d["occ_key"] + "_" + d["ano_arquivo_origem"].astype(str),
            id_municipio=lambda d: d["cod_ibge"].fillna(MUNICIPIO_NAO_IDENTIFICADO),
            inicio_ocorrencia=lambda d: d["dth_inicio_ocorrencia_aberta"],
            fim_ocorrencia=lambda d: d["dth_fim_ocorrencia_aberta"],
            tempo_preparacao=lambda d: d["mda_preparo"],
            tempo_deslocamento=lambda d: d["mda_deslocamento"],
            tempo_execucao=lambda d: d["mda_execucao"],
        )[[
            "num_ocorrencia_origem", "id_municipio", "id_causa", "id_conjunto",
            "inicio_ocorrencia", "fim_ocorrencia", "tempo_preparacao",
            "tempo_deslocamento", "tempo_execucao",
        ]]
    )

    # cod_ibge de município de outro estado (ou qualquer código não
    # cadastrado) vira o sentinela, para não violar a FK.
    ocorrencia_matched["id_municipio"] = ocorrencia_matched["id_municipio"].where(
        ocorrencia_matched["id_municipio"].isin(municipios_validos), MUNICIPIO_NAO_IDENTIFICADO
    )

    nao_casadas = interr[~casadas].copy()
    ocorrencia_pseudo = nao_casadas.assign(
        # mesmo raciocínio: num_ordem_interrupcao também é numerado por ano,
        # então compõe com o ano para não colidir entre anos diferentes.
        num_ocorrencia_origem=lambda d: d["num_ordem_interrupcao"] + "_" + d["ano_arquivo_origem"].astype(str),
        id_municipio=MUNICIPIO_NAO_IDENTIFICADO,
        inicio_ocorrencia=None,
        fim_ocorrencia=None,
        tempo_preparacao=None,
        tempo_deslocamento=None,
        tempo_execucao=None,
    )[[
        "num_ocorrencia_origem", "id_municipio", "id_causa", "id_conjunto",
        "inicio_ocorrencia", "fim_ocorrencia", "tempo_preparacao",
        "tempo_deslocamento", "tempo_execucao",
    ]]

    ocorrencia_final = pd.concat([ocorrencia_matched, ocorrencia_pseudo], ignore_index=True)
    print(f"\nGravando dados.ocorrencia ({len(ocorrencia_final):,} linhas: "
          f"{len(ocorrencia_matched):,} reais + {len(ocorrencia_pseudo):,} substitutas) ...")
    ocorrencia_final.to_sql(
        "ocorrencia", engine, schema="dados", if_exists="append", index=False, method="multi", chunksize=5000
    )

    # -------------------------------------------------------------
    # dados.interrupcao -- 1 linha por linha de staging.interrupcoes,
    # religando ao id_ocorrencia recém-criado.
    # -------------------------------------------------------------
    ocorrencia_ids = pd.read_sql("SELECT id_ocorrencia, num_ocorrencia_origem FROM dados.ocorrencia", engine)

    # mesma composição usada acima para montar num_ocorrencia_origem, senão o
    # merge abaixo não casa nenhuma linha.
    interr["chave_ocorrencia"] = (
        interr["occ_key"].where(casadas, interr["num_ordem_interrupcao"])
        + "_" + interr["ano_arquivo_origem"].astype(str)
    )
    interr = interr.merge(
        ocorrencia_ids, how="left", left_on="chave_ocorrencia", right_on="num_ocorrencia_origem"
    )

    interrupcao_final = interr.rename(
        columns={
            "num_unidade_consumidora": "consumidores_afetados",
            "dat_inicio_interrupcao": "inicio_interrupcao",
            "dat_fim_interrupcao": "fim_interrupcao",
        }
    )[["num_ordem_interrupcao", "id_ocorrencia", "consumidores_afetados", "inicio_interrupcao", "fim_interrupcao"]]
    interrupcao_final = interrupcao_final.rename(columns={"num_ordem_interrupcao": "num_ordem_interrupcao_origem"})

    print(f"Gravando dados.interrupcao ({len(interrupcao_final):,} linhas) ...")
    interrupcao_final.to_sql(
        "interrupcao", engine, schema="dados", if_exists="append", index=False, method="multi", chunksize=5000
    )

    print("\nOK -- transformação concluída.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--municipios", required=True,
        help="Caminho do CSV de referência dos municípios de PE (municipios_pe_ibge.csv)",
    )
    args = parser.parse_args()

    engine = pedir_conexao()
    ref_municipios = carregar_referencia_municipios(args.municipios)

    limpar_tabelas_dados(engine)
    montar_municipio(engine, ref_municipios)
    montar_causa(engine)
    montar_conjunto_eletrico(engine)

    try:
        montar_ocorrencia_e_interrupcao(engine)
    except Exception as e:
        # Grava o erro completo direto num arquivo, em vez de depender do
        # terminal mostrar/capturar tudo (o terminal costuma cortar saídas
        # muito grandes, principalmente com o INSERT + parâmetros gigantes).
        with open("erro_transformacao.txt", "w", encoding="utf-8") as f:
            f.write("=== str(erro) ===\n")
            f.write(str(e))
            f.write("\n\n=== traceback completo ===\n")
            f.write(traceback.format_exc())
        print("\n" + "=" * 60)
        print("ERRO ao montar dados.ocorrencia / dados.interrupcao.")
        print("O texto completo do erro foi salvo em: erro_transformacao.txt")
        print("(na mesma pasta de onde você rodou o script)")
        print("Me envie esse arquivo.")
        print("=" * 60)
        raise SystemExit(1)

    print("\nResumo final:")
    with engine.begin() as conn:
        for tabela in ["municipio", "causa", "conjunto_eletrico", "ocorrencia", "interrupcao"]:
            n = conn.execute(text(f"SELECT COUNT(*) FROM dados.{tabela}")).scalar()
            print(f"  dados.{tabela}: {n:,} linhas")
