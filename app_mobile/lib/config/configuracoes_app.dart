import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Configurações do app persistidas localmente: IP/porta do servidor Flask
/// no Raspberry Pi e a escala usada para gerar o JSON do mapa.
class ConfiguracoesApp extends ChangeNotifier {
  static const _chaveIp = 'servidor_ip';
  static const _chavePorta = 'servidor_porta';
  static const _chaveEscala = 'escala_metros_por_tile';
  static const _chaveLarguraPortaPadrao = 'largura_porta_padrao';
  static const _chaveLarguraJanelaPadrao = 'largura_janela_padrao';

  String ip = '192.168.0.100';
  int porta = 5000;
  double escalaMetrosPorTile = 0.1;
  double larguraPortaPadrao = 0.8;
  double larguraJanelaPadrao = 1.2;

  bool _carregado = false;
  bool get carregado => _carregado;

  Uri get urlUpload => Uri.parse('http://$ip:$porta/upload_map');

  Future<void> carregar() async {
    final prefs = await SharedPreferences.getInstance();
    ip = prefs.getString(_chaveIp) ?? ip;
    porta = prefs.getInt(_chavePorta) ?? porta;
    escalaMetrosPorTile = prefs.getDouble(_chaveEscala) ?? escalaMetrosPorTile;
    larguraPortaPadrao =
        prefs.getDouble(_chaveLarguraPortaPadrao) ?? larguraPortaPadrao;
    larguraJanelaPadrao =
        prefs.getDouble(_chaveLarguraJanelaPadrao) ?? larguraJanelaPadrao;
    _carregado = true;
    notifyListeners();
  }

  Future<void> salvar({
    required String ip,
    required int porta,
    required double escalaMetrosPorTile,
    required double larguraPortaPadrao,
    required double larguraJanelaPadrao,
  }) async {
    this.ip = ip;
    this.porta = porta;
    this.escalaMetrosPorTile = escalaMetrosPorTile;
    this.larguraPortaPadrao = larguraPortaPadrao;
    this.larguraJanelaPadrao = larguraJanelaPadrao;

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_chaveIp, ip);
    await prefs.setInt(_chavePorta, porta);
    await prefs.setDouble(_chaveEscala, escalaMetrosPorTile);
    await prefs.setDouble(_chaveLarguraPortaPadrao, larguraPortaPadrao);
    await prefs.setDouble(_chaveLarguraJanelaPadrao, larguraJanelaPadrao);

    notifyListeners();
  }
}
