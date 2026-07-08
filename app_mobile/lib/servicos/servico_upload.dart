import 'dart:convert';

import 'package:http/http.dart' as http;

import '../modelos/mapa_ambiente.dart';

class ResultadoUpload {
  final bool sucesso;
  final String mensagem;

  const ResultadoUpload({required this.sucesso, required this.mensagem});
}

/// Envia o mapa gerado para o servidor Flask do Raspberry Pi via
/// `POST /upload_map`.
class ServicoUpload {
  final Duration timeout;

  const ServicoUpload({this.timeout = const Duration(seconds: 10)});

  Future<ResultadoUpload> enviar({
    required Uri url,
    required MapaAmbiente mapa,
  }) async {
    try {
      final resposta = await http
          .post(
            url,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(mapa.toJson()),
          )
          .timeout(timeout);

      if (resposta.statusCode >= 200 && resposta.statusCode < 300) {
        return const ResultadoUpload(
          sucesso: true,
          mensagem: 'Mapa enviado com sucesso!',
        );
      }
      return ResultadoUpload(
        sucesso: false,
        mensagem: 'Servidor respondeu com erro ${resposta.statusCode}: '
            '${resposta.body}',
      );
    } catch (e) {
      return ResultadoUpload(
        sucesso: false,
        mensagem: 'Falha ao conectar ao servidor: $e',
      );
    }
  }
}
