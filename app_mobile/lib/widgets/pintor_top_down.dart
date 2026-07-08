import 'package:flutter/material.dart';

import '../modelos/mapa_ambiente.dart';

/// Renderiza uma prévia 2D top-down do mapa usando retângulos/linhas
/// coloridas como placeholder. Quando os PNGs do tileset forem fornecidos,
/// basta substituir os `Paint`/`drawRect` abaixo por `canvas.drawImageRect`
/// com o sprite correspondente a cada tipo.
class PintorTopDown extends CustomPainter {
  final List<Segmento> paredes;
  final List<AberturaComLargura> portas;
  final List<AberturaComLargura> janelas;
  final List<ObjetoAmbiente> objetos;
  final List<Ponto2D> cadeiaParedeEmAndamento;

  static const corParede = Color(0xFF4A4A4A);
  static const corPorta = Color(0xFFB5651D);
  static const corJanela = Color(0xFF6EC6FF);
  static const corObjeto = Color(0xFFE6A817);
  static const corCadeiaEmAndamento = Color(0xFF8BC34A);

  PintorTopDown({
    required this.paredes,
    required this.portas,
    required this.janelas,
    required this.objetos,
    this.cadeiaParedeEmAndamento = const [],
  });

  @override
  void paint(Canvas canvas, Size size) {
    final limites = _calcularLimites();
    if (limites == null) {
      _desenharMensagemVazia(canvas, size);
      return;
    }

    const margemPx = 24.0;
    final larguraDisponivel = size.width - margemPx * 2;
    final alturaDisponivel = size.height - margemPx * 2;
    final larguraMundo = (limites.right - limites.left).clamp(0.01, double.infinity);
    final alturaMundo = (limites.bottom - limites.top).clamp(0.01, double.infinity);
    final escala = [
      larguraDisponivel / larguraMundo,
      alturaDisponivel / alturaMundo,
    ].reduce((a, b) => a < b ? a : b);

    Offset paraTela(Ponto2D p) {
      final x = margemPx + (p.x - limites.left) * escala;
      final y = margemPx + (p.y - limites.top) * escala;
      return Offset(x, y);
    }

    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF1B1B1B));

    final paintParede = Paint()
      ..color = corParede
      ..strokeWidth = 6
      ..strokeCap = StrokeCap.round;
    for (final segmento in paredes) {
      canvas.drawLine(paraTela(segmento.inicio), paraTela(segmento.fim), paintParede);
    }

    if (cadeiaParedeEmAndamento.length > 1) {
      final paintCadeia = Paint()
        ..color = corCadeiaEmAndamento
        ..strokeWidth = 3
        ..strokeCap = StrokeCap.round;
      for (var i = 0; i < cadeiaParedeEmAndamento.length - 1; i++) {
        canvas.drawLine(
          paraTela(cadeiaParedeEmAndamento[i]),
          paraTela(cadeiaParedeEmAndamento[i + 1]),
          paintCadeia,
        );
      }
    }

    final paintPorta = Paint()
      ..color = corPorta
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round;
    for (final porta in portas) {
      _desenharAbertura(canvas, paraTela(porta.posicao), paintPorta);
    }

    final paintJanela = Paint()
      ..color = corJanela
      ..strokeWidth = 8
      ..strokeCap = StrokeCap.round;
    for (final janela in janelas) {
      _desenharAbertura(canvas, paraTela(janela.posicao), paintJanela);
    }

    final paintObjeto = Paint()..color = corObjeto;
    for (final objeto in objetos) {
      final centro = paraTela(objeto.posicao);
      const tamanho = 14.0;
      canvas.drawRect(
        Rect.fromCenter(center: centro, width: tamanho, height: tamanho),
        paintObjeto,
      );
      _desenharRotulo(canvas, objeto.tipo, centro + const Offset(0, 10));
    }
  }

  void _desenharAbertura(Canvas canvas, Offset centro, Paint paint) {
    canvas.drawLine(
      centro - const Offset(8, 0),
      centro + const Offset(8, 0),
      paint,
    );
  }

  void _desenharRotulo(Canvas canvas, String texto, Offset posicao) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: texto,
        style: const TextStyle(color: Colors.white70, fontSize: 10),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(canvas, posicao - Offset(textPainter.width / 2, 0));
  }

  void _desenharMensagemVazia(Canvas canvas, Size size) {
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF1B1B1B));
    final textPainter = TextPainter(
      text: const TextSpan(
        text: 'Nenhum elemento marcado ainda',
        style: TextStyle(color: Colors.white54),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(
      canvas,
      Offset(
        (size.width - textPainter.width) / 2,
        (size.height - textPainter.height) / 2,
      ),
    );
  }

  Rect? _calcularLimites() {
    final pontos = <Ponto2D>[
      for (final s in paredes) ...[s.inicio, s.fim],
      for (final p in portas) p.posicao,
      for (final j in janelas) j.posicao,
      for (final o in objetos) o.posicao,
      ...cadeiaParedeEmAndamento,
    ];
    if (pontos.isEmpty) return null;

    var minX = pontos.first.x, maxX = pontos.first.x;
    var minY = pontos.first.y, maxY = pontos.first.y;
    for (final p in pontos) {
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }
    return Rect.fromLTRB(minX, minY, maxX, maxY);
  }

  @override
  bool shouldRepaint(covariant PintorTopDown oldDelegate) => true;
}
