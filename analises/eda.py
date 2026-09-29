import pandas as pd

# Ler os dados
df = pd.read_csv("dados/amostra/ocorrencias_pe_amostra.csv")

# Converter datas
df["dth_inicio"] = pd.to_datetime(df["dth_inicio"])
df["dth_fim"] = pd.to_datetime(df["dth_fim"])

# Criar duração em minutos
df["duracao_min"] = (
    df["dth_fim"] - df["dth_inicio"]
).dt.total_seconds() / 60

# Visão geral
print("Tamanho da base:")
print(df.shape)

print("\nInformações da base:")
print(df.info())

# Valores ausentes
print("\nValores ausentes:")
print(df.isna().sum().sort_values(ascending=False))

# Causas de origem
print("\nCausas de origem:")
print(df["causa_origem"].value_counts())

# Principais causas específicas
print("\nPrincipais causas específicas:")
print(df["causa_especifica"].value_counts(dropna=False).head(10))

# Estatísticas da duração
print("\nEstatísticas da duração:")
print(df["duracao_min"].describe())

# Duração por causa de origem
print("\nDuração por causa de origem:")
print(
    df.groupby("causa_origem")["duracao_min"]
      .agg(["count", "mean", "median", "min", "max"])
      .sort_values("median", ascending=False)
)

# Ocorrências por mês
df["mes"] = df["dth_inicio"].dt.to_period("M").astype(str)

print("\nOcorrências por mês:")
print(df["mes"].value_counts().sort_index())

# Tempos médios das etapas
print("\nTempo médio das etapas:")
print(
    df[["min_preparo", "min_deslocamento", "min_execucao"]].mean()
)