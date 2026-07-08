import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';

import '../config/configuracoes_app.dart';
import '../estado/sessao_mapeamento.dart';
import 'tela_ar.dart';
import 'tela_configuracoes.dart';

/// Tela de abertura do app: pede permissão de câmera e leva ao
/// escaneamento AR ou às configurações.
class TelaInicial extends StatelessWidget {
  const TelaInicial({super.key});

  Future<void> _iniciarEscaneamento(BuildContext context) async {
    final status = await Permission.camera.request();
    if (!status.isGranted) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('É necessário conceder acesso à câmera para escanear o ambiente.'),
          ),
        );
      }
      return;
    }

    if (!context.mounted) return;
    context.read<SessaoMapeamento>().reiniciar();
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const TelaAr()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final configuracoes = context.watch<ConfiguracoesApp>();

    return Scaffold(
      appBar: AppBar(title: const Text('Maptale')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.view_in_ar, size: 96, color: Colors.deepPurpleAccent),
              const SizedBox(height: 16),
              const Text(
                'Escaneie um ambiente em AR e envie o mapa para o jogo do Raspberry Pi.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Servidor atual: ${configuracoes.ip}:${configuracoes.porta}',
                style: const TextStyle(color: Colors.white54, fontSize: 12),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _iniciarEscaneamento(context),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Iniciar escaneamento'),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const TelaConfiguracoes()),
                  ),
                  icon: const Icon(Icons.settings),
                  label: const Text('Configurações'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
