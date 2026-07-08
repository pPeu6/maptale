import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/configuracoes_app.dart';
import '../estado/sessao_mapeamento.dart';
import '../servicos/servico_upload.dart';
import '../widgets/pintor_top_down.dart';

/// Mostra a prévia 2D top-down do mapa e permite enviar o JSON final para
/// o servidor Flask do Raspberry Pi.
class TelaPreview extends StatefulWidget {
  const TelaPreview({super.key});

  @override
  State<TelaPreview> createState() => _TelaPreviewState();
}

class _TelaPreviewState extends State<TelaPreview> {
  final _controladorNome = TextEditingController(text: 'meu_ambiente');
  final _servicoUpload = const ServicoUpload();
  bool _enviando = false;

  @override
  void dispose() {
    _controladorNome.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    final sessao = context.read<SessaoMapeamento>();
    final configuracoes = context.read<ConfiguracoesApp>();
    final nome = _controladorNome.text.trim();

    if (nome.isEmpty) {
      _mostrarMensagem('Informe um nome para o ambiente.');
      return;
    }

    final mapa = sessao.finalizar(
      nomeAmbiente: nome,
      escalaMetrosPorTile: configuracoes.escalaMetrosPorTile,
    );

    setState(() => _enviando = true);
    final resultado = await _servicoUpload.enviar(
      url: configuracoes.urlUpload,
      mapa: mapa,
    );
    if (!mounted) return;
    setState(() => _enviando = false);
    _mostrarMensagem(resultado.mensagem);
  }

  void _mostrarMensagem(String mensagem) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(mensagem)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final sessao = context.watch<SessaoMapeamento>();

    return Scaffold(
      appBar: AppBar(title: const Text('Prévia do mapa')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _controladorNome,
              decoration: const InputDecoration(
                labelText: 'Nome do ambiente',
                border: OutlineInputBorder(),
              ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: CustomPaint(
                painter: PintorTopDown(
                  paredes: sessao.paredes,
                  portas: sessao.portas,
                  janelas: sessao.janelas,
                  objetos: sessao.objetos,
                ),
                child: const SizedBox.expand(),
              ),
            ),
          ),
          _legenda(),
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _enviando ? null : _enviar,
                icon: _enviando
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.cloud_upload),
                label: Text(_enviando ? 'Enviando...' : 'Enviar'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _legenda() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Wrap(
        spacing: 16,
        children: [
          _itemLegenda(PintorTopDown.corParede, 'Parede'),
          _itemLegenda(PintorTopDown.corPorta, 'Porta'),
          _itemLegenda(PintorTopDown.corJanela, 'Janela'),
          _itemLegenda(PintorTopDown.corObjeto, 'Objeto'),
        ],
      ),
    );
  }

  Widget _itemLegenda(Color cor, String rotulo) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 12, height: 12, color: cor),
        const SizedBox(width: 4),
        Text(rotulo, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}
