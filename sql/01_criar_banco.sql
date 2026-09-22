-- =====================================================================
-- Bússola de Crise — Neoenergia PE
-- Banco NOVO para o recorte de 2021 a 2025 (5 anos completos) + 1º semestre
-- de 2026, modelagem revisada (período ampliado no canvas do projeto)
-- =====================================================================
-- IMPORTANTE: CREATE DATABASE não pode rodar na mesma transação/sessão
-- que outros comandos DDL. Rode este arquivo conectado ao banco
-- "postgres" (ou outro banco de manutenção), e SÓ ELE.
--
-- Exemplo via psql:
--   psql -U postgres -h localhost -d postgres -f 01_criar_banco.sql
-- =====================================================================

CREATE DATABASE bussola_de_crise
    WITH ENCODING = 'UTF8'
    TEMPLATE = template0;

-- É só isso neste arquivo. A criação dos schemas (staging/dados) está no
-- início do 02_criar_tabelas_e_schemas.sql, não aqui -- porque CREATE
-- SCHEMA precisa rodar já conectado ao banco bussola_de_crise, e uma
-- conexão de banco de dados não muda sozinha de banco no meio do mesmo
-- script/execução (no DBeaver, mesmo rodando os dois blocos deste arquivo
-- em sequência, o CREATE SCHEMA acabaria indo para o banco errado se
-- ficasse aqui).
--
-- Depois de rodar este arquivo (conectado ao banco "postgres"), troque
-- para uma conexão/aba apontando para bussola_de_crise antes de abrir e
-- rodar o 02_criar_tabelas_e_schemas.sql.
