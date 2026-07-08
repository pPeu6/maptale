import 'package:ar_flutter_plugin_plus/datatypes/hittest_result_types.dart';
import 'package:ar_flutter_plugin_plus/models/ar_hittest_result.dart';
import 'package:vector_math/vector_math_64.dart' as vm;

import '../modelos/mapa_ambiente.dart';

/// Converte resultados de hit-test da AR (`ARHitTestResult`) em coordenadas
/// 2D (x, y) em metros, no plano top-down do schema compartilhado.
///
/// A AR trabalha em um espaço 3D (x, y, z) onde `y` é a altura (eixo
/// vertical). Para uma planta baixa, usamos o plano horizontal formado por
/// `x` e `z`. O primeiro toque bem-sucedido define a origem (0, 0); todos os
/// pontos seguintes são relativos a ela, conforme pedido no enunciado.
class ConversorCoordenadasAR {
  vm.Vector3? _origemMundo;

  bool get temOrigem => _origemMundo != null;

  /// Reinicia a origem, útil ao começar um novo escaneamento.
  void reiniciar() {
    _origemMundo = null;
  }

  /// Extrai a translação (posição) do resultado de hit-test mais próximo do
  /// tipo `plane`. Retorna `null` se não houver nenhum resultado de plano.
  vm.Vector3? _posicaoMundo(List<ARHitTestResult> resultados) {
    for (final resultado in resultados) {
      if (resultado.type == ARHitTestResultType.plane) {
        return resultado.worldTransform.getTranslation();
      }
    }
    return null;
  }

  /// Converte a lista de resultados de um toque em um [Ponto2D] relativo à
  /// origem do escaneamento. Retorna `null` se nenhum plano foi atingido.
  Ponto2D? converter(List<ARHitTestResult> resultadosHitTest) {
    final posicao = _posicaoMundo(resultadosHitTest);
    if (posicao == null) return null;

    _origemMundo ??= posicao;

    final x = posicao.x - _origemMundo!.x;
    final y = posicao.z - _origemMundo!.z; // z do AR vira "y" da planta baixa
    return Ponto2D(x, y);
  }
}
