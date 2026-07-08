import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/configuracoes_app.dart';
import 'estado/sessao_mapeamento.dart';
import 'telas/tela_inicial.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final configuracoes = ConfiguracoesApp();
  await configuracoes.carregar();
  runApp(AppMaptale(configuracoes: configuracoes));
}

class AppMaptale extends StatelessWidget {
  final ConfiguracoesApp configuracoes;

  const AppMaptale({super.key, required this.configuracoes});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<ConfiguracoesApp>.value(value: configuracoes),
        ChangeNotifierProvider<SessaoMapeamento>(
          create: (_) => SessaoMapeamento(
            larguraPortaPadrao: configuracoes.larguraPortaPadrao,
            larguraJanelaPadrao: configuracoes.larguraJanelaPadrao,
          ),
        ),
      ],
      child: MaterialApp(
        title: 'Maptale',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorSchemeSeed: Colors.deepPurple,
          brightness: Brightness.dark,
          useMaterial3: true,
        ),
        home: const TelaInicial(),
      ),
    );
  }
}
