import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/configuracoes_app.dart';

/// Tela de configurações: IP/porta do servidor Flask no Raspberry Pi,
/// escala do mapa e larguras padrão de porta/janela.
class TelaConfiguracoes extends StatefulWidget {
  const TelaConfiguracoes({super.key});

  @override
  State<TelaConfiguracoes> createState() => _TelaConfiguracoesState();
}

class _TelaConfiguracoesState extends State<TelaConfiguracoes> {
  late final TextEditingController _ip;
  late final TextEditingController _porta;
  late final TextEditingController _escala;
  late final TextEditingController _larguraPorta;
  late final TextEditingController _larguraJanela;

  @override
  void initState() {
    super.initState();
    final config = context.read<ConfiguracoesApp>();
    _ip = TextEditingController(text: config.ip);
    _porta = TextEditingController(text: config.porta.toString());
    _escala = TextEditingController(text: config.escalaMetrosPorTile.toString());
    _larguraPorta = TextEditingController(text: config.larguraPortaPadrao.toString());
    _larguraJanela = TextEditingController(text: config.larguraJanelaPadrao.toString());
  }

  @override
  void dispose() {
    _ip.dispose();
    _porta.dispose();
    _escala.dispose();
    _larguraPorta.dispose();
    _larguraJanela.dispose();
    super.dispose();
  }

  Future<void> _salvar() async {
    final config = context.read<ConfiguracoesApp>();
    final porta = int.tryParse(_porta.text.trim());
    final escala = double.tryParse(_escala.text.trim().replaceAll(',', '.'));
    final larguraPorta = double.tryParse(_larguraPorta.text.trim().replaceAll(',', '.'));
    final larguraJanela = double.tryParse(_larguraJanela.text.trim().replaceAll(',', '.'));

    if (_ip.text.trim().isEmpty ||
        porta == null ||
        escala == null ||
        escala <= 0 ||
        larguraPorta == null ||
        larguraJanela == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Verifique os valores informados.')),
      );
      return;
    }

    await config.salvar(
      ip: _ip.text.trim(),
      porta: porta,
      escalaMetrosPorTile: escala,
      larguraPortaPadrao: larguraPorta,
      larguraJanelaPadrao: larguraJanela,
    );

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Configurações salvas.')),
    );
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Configurações')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Servidor (jogo no Raspberry Pi)',
              style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(
            controller: _ip,
            decoration: const InputDecoration(labelText: 'IP do servidor', border: OutlineInputBorder()),
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _porta,
            decoration: const InputDecoration(labelText: 'Porta', border: OutlineInputBorder()),
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 24),
          const Text('Mapa', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          TextField(
            controller: _escala,
            decoration: const InputDecoration(
              labelText: 'Escala (metros por tile)',
              border: OutlineInputBorder(),
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _larguraPorta,
            decoration: const InputDecoration(
              labelText: 'Largura padrão de porta (m)',
              border: OutlineInputBorder(),
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _larguraJanela,
            decoration: const InputDecoration(
              labelText: 'Largura padrão de janela (m)',
              border: OutlineInputBorder(),
            ),
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: 24),
          ElevatedButton(onPressed: _salvar, child: const Text('Salvar')),
        ],
      ),
    );
  }
}
