# Pseudocodigo - Janela de Plantio

```text
REGRA DE JANELA DE PLANTIO:
  SE data_plantio estiver vazia ou invalida:
    orientacao = "SEM_DADO"
    sistema_recomendado = "nenhum"
    regra_acionada = "dado_ausente_data_plantio"

  SENAO SE mes_plantio >= 1 E mes_plantio <= 3:
    orientacao = "JANELA_APTA"
    sistema_recomendado = "cana_ano_e_meio"
    regra_acionada = "mes_jan_mar_ano_e_meio"

  SENAO SE mes_plantio >= 4 E mes_plantio <= 8:
    orientacao = "JANELA_INVERNO"
    sistema_recomendado = "plantio_inverno"
    regra_acionada = "mes_abr_ago_inverno"

  SENAO SE mes_plantio >= 9 E mes_plantio <= 11:
    orientacao = "JANELA_APTA"
    sistema_recomendado = "cana_de_ano"
    regra_acionada = "mes_set_nov_cana_de_ano"

  SENAO:
    orientacao = "ATENCAO"
    sistema_recomendado = "fora_janela_preferencial"
    regra_acionada = "mes_dez_fora_janela_preferencial"

  preparo_solo_inicio = data_plantio - 150 dias
  corretivos_inicio = data_plantio - 90 dias
  corretivos_fim = data_plantio - 60 dias
```

```text
REGRA DE SISTEMA INFORMADO:
  SE sistema_informado contem "18" OU "ano e meio":
    sistema_recomendado = "cana_ano_e_meio"
    regra_acionada = "sistema_informado_ano_e_meio"

  SENAO SE sistema_informado contem "inverno":
    sistema_recomendado = "plantio_inverno"
    regra_acionada = "sistema_informado_inverno"

  SENAO SE sistema_informado contem "12" OU "ano":
    sistema_recomendado = "cana_de_ano"
    regra_acionada = "sistema_informado_cana_de_ano"

  SENAO:
    usar regra de janela de plantio pelo mes
```

```text
REGRA DE COLHEITA POS-PLANTIO:
  SE data_colheita estiver vazia ou invalida:
    orientacao = "SEM_DADO"
    regra_acionada = "dado_ausente_data_colheita"

  SENAO SE mes_colheita >= 5 E mes_colheita <= 11:
    orientacao = "COLHEITA_NA_JANELA"
    regra_acionada = "colheita_maio_novembro"

  SENAO:
    orientacao = "ATENCAO"
    regra_acionada = "colheita_fora_maio_novembro"
```
