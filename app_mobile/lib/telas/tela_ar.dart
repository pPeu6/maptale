import 'package:ar_flutter_plugin_plus/ar_flutter_plugin_plus.dart';
import 'package:ar_flutter_plugin_plus/datatypes/config_planedetection.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_anchor_manager.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_location_manager.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_object_manager.dart';
import 'package:ar_flutter_plugin_plus/managers/ar_session_manager.dart';
import 'package:ar_flutter_plugin_plus/models/ar_hittest_result.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/configuracoes_app.dart';
import '../estado/sessao_mapeamento.dart';
import '../servicos/conversor_coordenadas_ar.dart';
import '../widgets/barra_modos.dart';
import '../widgets/seletor_tipo_objeto.dart';
import 'tela_configuracoes.dart';
import 'tela_preview.dart';

/// Tela principal: câmera em modo AR com detecção de plano no chão. Cada
/// toque na área detectada é convertido em coordenadas (x, y) do schema e
/// registrado na [SessaoMapeamento] de acordo com o modo ativo.
class TelaAr extends StatefulWidget {
  const TelaAr({super.key});

  @override
  State<TelaAr> createState() => _TelaArState();
}

class _TelaArState extends State<TelaAr> {
  ARSessionManager? _arSessionManager;
  ARObjectManager? _arObjectManager;
  final _conversor = ConversorCoordenadasAR();

  @override
  void dispose() {
    _arSessionManager?.dispose();
    super.dispose();
  }

  void _aoCriarArView(
    ARSessionManager sessionManager,
    ARObjectManager objectManager,
    ARAnchorManager anchorManager,
    ARLocationManager locationManager,
  ) {
    _arSessionManager = sessionManager;
    _arObjectManager = objectManager;

    _arSessionManager!.onInitialize(
      showFeaturePoints: false,
      showPlanes: true,
      showWorldOrigin: false,
      handleTaps: true,
    );
    _arObjectManager!.onInitialize();
    _arSessionManager!.onPlaneOrPointTap = _aoTocarNoPlano;
  }

  Future<void> _aoTocarNoPlano(List<ARHitTestResult> resultados) async {
    final ponto = _conversor.converter(resultados);
    if (ponto == null) return;

    if (!mounted) return;
    context.read<SessaoMapeamento>().registrarToque(ponto);
  }

  void _abrirConfiguracoes() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const TelaConfiguracoes()),
    );
  }

  void _finalizarEscaneamento() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const TelaPreview()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final sessao = context.watch<SessaoMapeamento>();
    final configuracoes = context.watch<ConfiguracoesApp>();

    return Scaffold(
      body: Stack(
        children: [
          ARView(
            onARViewCreated: _aoCriarArView,
            planeDetectionConfig: PlaneDetectionConfig.horizontal,
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _painelInfo(sessao),
                  IconButton(
                    onPressed: _abrirConfiguracoes,
                    icon: const Icon(Icons.settings, color: Colors.white),
                    style: IconButton.styleFrom(backgroundColor: Colors.black45),
                  ),
                ],
              ),
            ),
          ),
          if (sessao.modo == ModoMapeamento.objeto)
            Positioned(
              top: 80,
              left: 0,
              right: 0,
              child: const SeletorTipoObjeto(),
            ),
          Align(
            alignment: Alignment.bottomCenter,
            child: BarraModos(aoFinalizar: _finalizarEscaneamento),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          _conversor.reiniciar();
          sessao.reiniciar();
        },
        backgroundColor: Colors.redAccent,
        icon: const Icon(Icons.refresh),
        label: const Text('Reiniciar'),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.startFloat,
      extendBody: true,
      backgroundColor: configuracoes.carregado ? null : Colors.black,
    );
  }

  Widget _painelInfo(SessaoMapeamento sessao) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black45,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Modo: ${_rotuloModo(sessao.modo)}',
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          Text(
            'Pontos marcados: ${sessao.totalPontosMarcados}',
            style: const TextStyle(color: Colors.white70, fontSize: 12),
          ),
          if (sessao.ultimoPonto != null)
            Text(
              'Último: ${sessao.ultimoPonto}',
              style: const TextStyle(color: Colors.white70, fontSize: 12),
            ),
        ],
      ),
    );
  }

  String _rotuloModo(ModoMapeamento modo) {
    switch (modo) {
      case ModoMapeamento.parede:
        return 'Desenhar parede';
      case ModoMapeamento.porta:
        return 'Marcar porta';
      case ModoMapeamento.janela:
        return 'Marcar janela';
      case ModoMapeamento.objeto:
        return 'Marcar objeto';
    }
  }
}
