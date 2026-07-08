import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../estado/sessao_mapeamento.dart';

/// Barra inferior com os botões de troca de modo (parede/porta/janela/
/// objeto) e as ações de desfazer/novo segmento/fechar polígono/finalizar.
class BarraModos extends StatelessWidget {
  final VoidCallback aoFinalizar;

  const BarraModos({super.key, required this.aoFinalizar});

  @override
  Widget build(BuildContext context) {
    final sessao = context.watch<SessaoMapeamento>();

    return Material(
      color: Colors.black87,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _botaoModo(
                    contexto: context,
                    modo: ModoMapeamento.parede,
                    icone: Icons.linear_scale,
                    rotulo: 'Parede',
                  ),
                  _botaoModo(
                    contexto: context,
                    modo: ModoMapeamento.porta,
                    icone: Icons.door_front_door_outlined,
                    rotulo: 'Porta',
                  ),
                  _botaoModo(
                    contexto: context,
                    modo: ModoMapeamento.janela,
                    icone: Icons.window_outlined,
                    rotulo: 'Janela',
                  ),
                  _botaoModo(
                    contexto: context,
                    modo: ModoMapeamento.objeto,
                    icone: Icons.chair_outlined,
                    rotulo: 'Objeto',
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  TextButton.icon(
                    onPressed: sessao.podeDesfazer ? sessao.desfazer : null,
                    icon: const Icon(Icons.undo, color: Colors.white70),
                    label: const Text('Desfazer', style: TextStyle(color: Colors.white70)),
                  ),
                  if (sessao.modo == ModoMapeamento.parede) ...[
                    TextButton.icon(
                      onPressed: sessao.cadeiaParedeAtual.isEmpty
                          ? null
                          : sessao.novoSegmentoParede,
                      icon: const Icon(Icons.call_split, color: Colors.white70),
                      label: const Text('Novo segmento', style: TextStyle(color: Colors.white70)),
                    ),
                    TextButton.icon(
                      onPressed: sessao.podeFecharPoligono ? sessao.fecharPoligono : null,
                      icon: const Icon(Icons.change_history, color: Colors.white70),
                      label: const Text('Fechar', style: TextStyle(color: Colors.white70)),
                    ),
                  ],
                  ElevatedButton.icon(
                    onPressed: aoFinalizar,
                    icon: const Icon(Icons.check),
                    label: const Text('Finalizar'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _botaoModo({
    required BuildContext contexto,
    required ModoMapeamento modo,
    required IconData icone,
    required String rotulo,
  }) {
    final sessao = contexto.watch<SessaoMapeamento>();
    final selecionado = sessao.modo == modo;
    return InkWell(
      onTap: () => sessao.definirModo(modo),
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Column(
          children: [
            Icon(icone, color: selecionado ? Colors.amber : Colors.white),
            Text(
              rotulo,
              style: TextStyle(
                color: selecionado ? Colors.amber : Colors.white,
                fontWeight: selecionado ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
