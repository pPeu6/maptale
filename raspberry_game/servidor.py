"""Servidor Flask que recebe o mapa escaneado pelo app mobile (POST
/upload_map) e o salva em disco. Pode rodar sozinho (para testes) ou ser
integrado ao loop do jogo por `jogo/principal.py`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable, Optional

from flask import Flask, jsonify, request

from mapa.esquema import ErroValidacaoMapa, validar_mapa

logger = logging.getLogger(__name__)

AoReceberMapa = Callable[[dict], None]


def criar_app(pasta_mapas: Path, ao_receber_mapa: Optional[AoReceberMapa] = None) -> Flask:
    """Factory da aplicação Flask, para permitir injetar a pasta de destino
    e um callback (usado por `principal.py` para recarregar o mapa no jogo
    assim que um novo upload chega, sem precisar reiniciar)."""
    app = Flask(__name__)
    pasta_mapas.mkdir(parents=True, exist_ok=True)

    @app.post("/upload_map")
    def upload_map():
        dados = request.get_json(silent=True)
        try:
            validar_mapa(dados)
        except ErroValidacaoMapa as erro:
            logger.warning("Mapa rejeitado: %s", erro)
            return jsonify({"erro": str(erro)}), 400

        nome_arquivo = f"{dados['nome_ambiente']}.json"
        caminho = pasta_mapas / nome_arquivo
        caminho.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("Mapa '%s' salvo em %s", dados["nome_ambiente"], caminho)

        if ao_receber_mapa is not None:
            try:
                ao_receber_mapa(dados)
            except Exception:
                logger.exception("Falha ao notificar o jogo sobre o novo mapa")

        return jsonify({"status": "ok", "arquivo": nome_arquivo}), 200

    @app.get("/status")
    def status():
        return jsonify({"status": "online"}), 200

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pasta_mapas_padrao = Path(__file__).resolve().parent / "mapas"
    app = criar_app(pasta_mapas_padrao)
    app.run(host="0.0.0.0", port=5000)
