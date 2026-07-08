"""Validação manual do JSON compartilhado (ver ../../schema/mapa.schema.json).

Evitamos dependências pesadas (ex.: pydantic/jsonschema) para manter o
processo leve no Raspberry Pi 3 - a validação abaixo é suficiente para o
contrato combinado entre as três partes do sistema.
"""

from __future__ import annotations

from typing import Any


class ErroValidacaoMapa(Exception):
    """Levantada quando o JSON recebido não segue o schema combinado."""


def _validar_ponto2d(valor: Any, contexto: str) -> None:
    if not isinstance(valor, (list, tuple)) or len(valor) != 2:
        raise ErroValidacaoMapa(f"{contexto} deve ser uma lista [x, y]")
    for coordenada in valor:
        if not isinstance(coordenada, (int, float)):
            raise ErroValidacaoMapa(f"{contexto} deve conter apenas números")


def _validar_segmento(valor: Any, indice: int) -> None:
    if not isinstance(valor, dict):
        raise ErroValidacaoMapa(f"paredes[{indice}] deve ser um objeto")
    for chave in ("inicio", "fim"):
        if chave not in valor:
            raise ErroValidacaoMapa(f"paredes[{indice}] precisa da chave '{chave}'")
        _validar_ponto2d(valor[chave], f"paredes[{indice}].{chave}")


def _validar_abertura(valor: Any, campo: str, indice: int) -> None:
    if not isinstance(valor, dict):
        raise ErroValidacaoMapa(f"{campo}[{indice}] deve ser um objeto")
    if "posicao" not in valor:
        raise ErroValidacaoMapa(f"{campo}[{indice}] precisa da chave 'posicao'")
    _validar_ponto2d(valor["posicao"], f"{campo}[{indice}].posicao")

    largura = valor.get("largura")
    if not isinstance(largura, (int, float)) or largura <= 0:
        raise ErroValidacaoMapa(f"{campo}[{indice}].largura deve ser um número positivo")


def _validar_objeto(valor: Any, indice: int) -> None:
    if not isinstance(valor, dict):
        raise ErroValidacaoMapa(f"objetos[{indice}] deve ser um objeto")
    tipo = valor.get("tipo")
    if not isinstance(tipo, str) or not tipo.strip():
        raise ErroValidacaoMapa(f"objetos[{indice}].tipo deve ser uma string não vazia")
    if "posicao" not in valor:
        raise ErroValidacaoMapa(f"objetos[{indice}] precisa da chave 'posicao'")
    _validar_ponto2d(valor["posicao"], f"objetos[{indice}].posicao")


def validar_mapa(dados: Any) -> None:
    """Valida `dados` contra o schema compartilhado.

    Levanta `ErroValidacaoMapa` com uma mensagem descritiva caso algo esteja
    fora do esperado. Não retorna nada quando os dados são válidos.
    """
    if not isinstance(dados, dict):
        raise ErroValidacaoMapa("o corpo da requisição deve ser um objeto JSON")

    campos_obrigatorios = (
        "nome_ambiente",
        "escala_metros_por_tile",
        "paredes",
        "portas",
        "janelas",
        "objetos",
    )
    for campo in campos_obrigatorios:
        if campo not in dados:
            raise ErroValidacaoMapa(f"campo obrigatório ausente: '{campo}'")

    nome = dados["nome_ambiente"]
    if not isinstance(nome, str) or not nome.strip():
        raise ErroValidacaoMapa("'nome_ambiente' deve ser uma string não vazia")

    escala = dados["escala_metros_por_tile"]
    if not isinstance(escala, (int, float)) or escala <= 0:
        raise ErroValidacaoMapa("'escala_metros_por_tile' deve ser um número positivo")

    paredes = dados["paredes"]
    if not isinstance(paredes, list):
        raise ErroValidacaoMapa("'paredes' deve ser uma lista")
    for indice, segmento in enumerate(paredes):
        _validar_segmento(segmento, indice)

    for campo in ("portas", "janelas"):
        valores = dados[campo]
        if not isinstance(valores, list):
            raise ErroValidacaoMapa(f"'{campo}' deve ser uma lista")
        for indice, abertura in enumerate(valores):
            _validar_abertura(abertura, campo, indice)

    objetos = dados["objetos"]
    if not isinstance(objetos, list):
        raise ErroValidacaoMapa("'objetos' deve ser uma lista")
    for indice, objeto in enumerate(objetos):
        _validar_objeto(objeto, indice)
