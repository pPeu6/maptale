import 'package:flutter/foundation.dart';

import '../modelos/mapa_ambiente.dart';

enum ModoMapeamento { parede, porta, janela, objeto }

/// Estado central do escaneamento: guarda o modo atual de marcação e todos
/// os elementos já registrados (paredes, portas, janelas, objetos),
/// expondo as operações necessárias para cada modo descrito no enunciado.
class SessaoMapeamento extends ChangeNotifier {
  ModoMapeamento modo = ModoMapeamento.parede;

  final List<Segmento> paredes = [];
  final List<AberturaComLargura> portas = [];
  final List<AberturaComLargura> janelas = [];
  final List<ObjetoAmbiente> objetos = [];

  /// Pontos da cadeia de parede que ainda está sendo desenhada (conecta
  /// toques sequenciais até que "novo segmento" ou "fechar polígono" seja
  /// chamado).
  final List<Ponto2D> cadeiaParedeAtual = [];

  TipoObjeto tipoObjetoSelecionado = TipoObjeto.sofa;
  double larguraPorta;
  double larguraJanela;

  Ponto2D? ultimoPonto;

  final List<void Function()> _historico = [];

  SessaoMapeamento({
    double larguraPortaPadrao = 0.8,
    double larguraJanelaPadrao = 1.2,
  })  : larguraPorta = larguraPortaPadrao,
        larguraJanela = larguraJanelaPadrao;

  bool get podeFecharPoligono => cadeiaParedeAtual.length >= 3;
  bool get podeDesfazer => _historico.isNotEmpty;

  int get totalPontosMarcados =>
      paredes.length + portas.length + janelas.length + objetos.length;

  void definirModo(ModoMapeamento novoModo) {
    modo = novoModo;
    notifyListeners();
  }

  void definirTipoObjeto(TipoObjeto tipo) {
    tipoObjetoSelecionado = tipo;
    notifyListeners();
  }

  void definirLarguraPorta(double largura) {
    larguraPorta = largura;
    notifyListeners();
  }

  void definirLarguraJanela(double largura) {
    larguraJanela = largura;
    notifyListeners();
  }

  /// Ponto de entrada único chamado pela tela de AR a cada toque
  /// convertido em coordenadas do schema.
  void registrarToque(Ponto2D ponto) {
    ultimoPonto = ponto;
    switch (modo) {
      case ModoMapeamento.parede:
        _registrarPontoParede(ponto);
        break;
      case ModoMapeamento.porta:
        _registrarAbertura(ponto, portas, larguraPorta);
        break;
      case ModoMapeamento.janela:
        _registrarAbertura(ponto, janelas, larguraJanela);
        break;
      case ModoMapeamento.objeto:
        _registrarObjeto(ponto);
        break;
    }
    notifyListeners();
  }

  void _registrarPontoParede(Ponto2D ponto) {
    if (cadeiaParedeAtual.isNotEmpty) {
      final anterior = cadeiaParedeAtual.last;
      final segmento = Segmento(inicio: anterior, fim: ponto);
      paredes.add(segmento);
      cadeiaParedeAtual.add(ponto);
      _historico.add(() {
        paredes.removeLast();
        cadeiaParedeAtual.removeLast();
      });
    } else {
      cadeiaParedeAtual.add(ponto);
      _historico.add(() {
        cadeiaParedeAtual.removeLast();
      });
    }
  }

  /// Portas/janelas devem ficar sobre uma parede já existente: o ponto
  /// tocado é projetado (snap) no segmento de parede mais próximo antes de
  /// ser salvo.
  void _registrarAbertura(
    Ponto2D ponto,
    List<AberturaComLargura> destino,
    double largura,
  ) {
    final posicaoFinal = _projetarNaParedeMaisProxima(ponto) ?? ponto;
    final abertura = AberturaComLargura(posicao: posicaoFinal, largura: largura);
    destino.add(abertura);
    _historico.add(() => destino.removeLast());
  }

  void _registrarObjeto(Ponto2D ponto) {
    final objeto = ObjetoAmbiente(tipo: tipoObjetoSelecionado.chave, posicao: ponto);
    objetos.add(objeto);
    _historico.add(() => objetos.removeLast());
  }

  Ponto2D? _projetarNaParedeMaisProxima(Ponto2D ponto) {
    if (paredes.isEmpty) return null;

    Ponto2D? melhorProjecao;
    double menorDistanciaQuadrada = double.infinity;

    for (final segmento in paredes) {
      final projecao = _projetarPontoNoSegmento(ponto, segmento);
      final dx = projecao.x - ponto.x;
      final dy = projecao.y - ponto.y;
      final distanciaQuadrada = dx * dx + dy * dy;
      if (distanciaQuadrada < menorDistanciaQuadrada) {
        menorDistanciaQuadrada = distanciaQuadrada;
        melhorProjecao = projecao;
      }
    }
    return melhorProjecao;
  }

  Ponto2D _projetarPontoNoSegmento(Ponto2D p, Segmento segmento) {
    final a = segmento.inicio;
    final b = segmento.fim;
    final abX = b.x - a.x;
    final abY = b.y - a.y;
    final comprimentoQuadrado = abX * abX + abY * abY;

    if (comprimentoQuadrado == 0) return a;

    final apX = p.x - a.x;
    final apY = p.y - a.y;
    var t = (apX * abX + apY * abY) / comprimentoQuadrado;
    t = t.clamp(0.0, 1.0);

    return Ponto2D(a.x + t * abX, a.y + t * abY);
  }

  /// Encerra a cadeia de parede atual sem fechar um polígono, permitindo
  /// começar a desenhar uma nova parede desconectada.
  void novoSegmentoParede() {
    if (cadeiaParedeAtual.isEmpty) return;
    cadeiaParedeAtual.clear();
    notifyListeners();
  }

  /// Fecha o polígono atual ligando o último ponto ao primeiro.
  void fecharPoligono() {
    if (!podeFecharPoligono) return;
    final primeiro = cadeiaParedeAtual.first;
    final ultimo = cadeiaParedeAtual.last;
    paredes.add(Segmento(inicio: ultimo, fim: primeiro));
    cadeiaParedeAtual.clear();
    notifyListeners();
  }

  void desfazer() {
    if (_historico.isEmpty) return;
    final desfazerUltimaAcao = _historico.removeLast();
    desfazerUltimaAcao();
    notifyListeners();
  }

  void reiniciar() {
    paredes.clear();
    portas.clear();
    janelas.clear();
    objetos.clear();
    cadeiaParedeAtual.clear();
    _historico.clear();
    ultimoPonto = null;
    notifyListeners();
  }

  MapaAmbiente finalizar({
    required String nomeAmbiente,
    required double escalaMetrosPorTile,
  }) {
    return MapaAmbiente(
      nomeAmbiente: nomeAmbiente,
      escalaMetrosPorTile: escalaMetrosPorTile,
      paredes: List.unmodifiable(paredes),
      portas: List.unmodifiable(portas),
      janelas: List.unmodifiable(janelas),
      objetos: List.unmodifiable(objetos),
    );
  }
}
