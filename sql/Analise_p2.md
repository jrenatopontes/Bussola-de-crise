# Pergunta 2 do canvas — Sazonalidade

**Pergunta:** "Quando elas acontecem: existe alguma sazonalidade ao longo dos meses
ou uma concentração em horários específicos do dia?"

**Base analisada:** `dados.interrupcao`, recorte 2021–2025 (5 anos completos; 2026
excluído da análise por mês para não distorcer a comparação, já que é só 1º semestre —
ver nota metodológica no final).

---

## 1. Sazonalidade por mês

| Mês | Interrupções | Consumidores afetados | Média por interrupção |
|---|---|---|---|
| Jan | 85.491 | 6.544.791 | 76,6 |
| Fev | 85.173 | 6.836.557 | 80,3 |
| Mar | **96.274** | 7.438.136 | 77,3 |
| Abr | 88.763 | 6.996.063 | 78,8 |
| Mai | 91.480 | 7.144.539 | 78,1 |
| Jun | 85.842 | 5.574.957 | 64,9 |
| Jul | 82.564 | 5.879.968 | 71,2 |
| Ago | 80.749 | 6.615.344 | 81,9 |
| Set | **74.908** | 6.117.538 | 81,7 |
| Out | 80.538 | 7.112.387 | **88,3** |
| Nov | 84.074 | 5.559.483 | 66,1 |
| Dez | 85.353 | 6.381.747 | 74,8 |

- **Pico de volume**: março (96.274) — período mais chuvoso do ano na região,
  consistente com a causa "MEIO AMBIENTE" liderando nesse mês (37.712 ocorrências,
  à frente de "PRÓPRIAS DO SISTEMA" com 33.933).
- **Vale de volume**: setembro (74.908), com o platô jul-out todo mais baixo.
- **Maior impacto médio por evento**: outubro (88,3 consumidores/interrupção) —
  mesmo não sendo o mês de maior volume. Investigado em detalhe na seção 3.

## 2. Sazonalidade por horário do dia

- **Pico**: 9h (101.682 interrupções), com toda a faixa 7h–11h concentrando o maior
  volume do dia.
- **Vale**: madrugada, principalmente 2h–4h (~8.300–9.300), cerca de 1/10 do pico.
- **Padrão**: sobe rapidamente a partir das 5h, platô alto entre 7h e 14h, decai
  gradualmente até a madrugada.

## 3. Por que outubro tem o maior impacto médio por evento?

**Hipóteses testadas e descartadas:**
- **Chuva**: outubro é um dos meses mais secos do ano (0,6mm/dia de média, a 2ª menor
  do ano) — não é o motivo.
- **Vento/rajadas**: rajada média de outubro (10,4 m/s) é próxima da maioria dos
  outros meses; dezembro tem a rajada máxima mais alta do ano (25,7 m/s) e não se
  destaca em impacto médio — não é o motivo.
- **Um único evento extremo distorcendo a média**: os 20 maiores eventos de outubro
  somam só 3,3% do total de consumidores afetados no mês, e aparecem espalhados em
  4 anos diferentes (2022–2025), não concentrados em um ano atípico — não é isso.

**Padrão real encontrado**: em outubro, a causa "PRÓPRIAS DO SISTEMA" (falha de
equipamento, sobrecarga, desligamento de segurança) lidera com 31.085 ocorrências,
à frente de "MEIO AMBIENTE" (24.180) — o oposto do que acontece em março, onde
"MEIO AMBIENTE" lidera (37.712 contra 33.933). Olhando a base toda, eventos de
"PRÓPRIAS DO SISTEMA" afetam em média 81,7 consumidores, contra 76,8 de "MEIO
AMBIENTE" — uma diferença real, mas modesta (~6%), que sozinha não explica toda a
diferença de outubro.

**Conclusão**: o impacto médio maior em outubro é um padrão recorrente (se repete
todo ano, não é acaso de um ano só) e parece estar ligado à maior proporção de causas
ligadas à própria rede elétrica nesse período — mas essa relação **não foi comprovada
como causa direta** com os dados disponíveis, só a correlação.


