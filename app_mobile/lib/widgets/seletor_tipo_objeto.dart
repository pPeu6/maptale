import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../estado/sessao_mapeamento.dart';
import '../modelos/mapa_ambiente.dart';

/// Dropdown com os tipos de objeto disponíveis, exibido apenas quando o
/// modo "objeto" está ativo.
class SeletorTipoObjeto extends StatelessWidget {
  const SeletorTipoObjeto({super.key});

  @override
  Widget build(BuildContext context) {
    final sessao = context.watch<SessaoMapeamento>();

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black54,
        borderRadius: BorderRadius.circular(8),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<TipoObjeto>(
          value: sessao.tipoObjetoSelecionado,
          dropdownColor: Colors.black87,
          iconEnabledColor: Colors.white,
          style: const TextStyle(color: Colors.white),
          items: TipoObjeto.todos
              .map((tipo) => DropdownMenuItem(
                    value: tipo,
                    child: Text(tipo.rotulo),
                  ))
              .toList(),
          onChanged: (tipo) {
            if (tipo != null) sessao.definirTipoObjeto(tipo);
          },
        ),
      ),
    );
  }
}
