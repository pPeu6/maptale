/// Modelos de dados que espelham o schema JSON compartilhado entre o app
/// mobile e o jogo do Raspberry Pi (ver `schema/mapa.schema.json` na raiz
/// do repositório).
library modelos.mapa_ambiente;

class Ponto2D {
  final double x;
  final double y;

  const Ponto2D(this.x, this.y);

  List<double> toJson() => [x, y];

  @override
  String toString() => '(${x.toStringAsFixed(2)}, ${y.toStringAsFixed(2)})';
}

class Segmento {
  final Ponto2D inicio;
  final Ponto2D fim;

  const Segmento({required this.inicio, required this.fim});

  Map<String, dynamic> toJson() => {
        'inicio': inicio.toJson(),
        'fim': fim.toJson(),
      };
}

class AberturaComLargura {
  final Ponto2D posicao;
  final double largura;

  const AberturaComLargura({required this.posicao, required this.largura});

  Map<String, dynamic> toJson() => {
        'posicao': posicao.toJson(),
        'largura': largura,
      };
}

class ObjetoAmbiente {
  final String tipo;
  final Ponto2D posicao;

  const ObjetoAmbiente({required this.tipo, required this.posicao});

  Map<String, dynamic> toJson() => {
        'tipo': tipo,
        'posicao': posicao.toJson(),
      };
}

/// Tipos de objetos disponíveis no dropdown de marcação. Livre para expandir
/// conforme necessário; o valor enviado ao backend é sempre a string em
/// `chave`.
class TipoObjeto {
  final String chave;
  final String rotulo;

  const TipoObjeto(this.chave, this.rotulo);

  static const sofa = TipoObjeto('sofa', 'Sofá');
  static const mesa = TipoObjeto('mesa', 'Mesa');
  static const cama = TipoObjeto('cama', 'Cama');
  static const cadeira = TipoObjeto('cadeira', 'Cadeira');
  static const armario = TipoObjeto('armario', 'Armário');
  static const geladeira = TipoObjeto('geladeira', 'Geladeira');
  static const pia = TipoObjeto('pia', 'Pia');

  static const todos = <TipoObjeto>[
    sofa,
    mesa,
    cama,
    cadeira,
    armario,
    geladeira,
    pia,
  ];
}

class MapaAmbiente {
  final String nomeAmbiente;
  final double escalaMetrosPorTile;
  final List<Segmento> paredes;
  final List<AberturaComLargura> portas;
  final List<AberturaComLargura> janelas;
  final List<ObjetoAmbiente> objetos;

  const MapaAmbiente({
    required this.nomeAmbiente,
    required this.escalaMetrosPorTile,
    required this.paredes,
    required this.portas,
    required this.janelas,
    required this.objetos,
  });

  Map<String, dynamic> toJson() => {
        'nome_ambiente': nomeAmbiente,
        'escala_metros_por_tile': escalaMetrosPorTile,
        'paredes': paredes.map((p) => p.toJson()).toList(),
        'portas': portas.map((p) => p.toJson()).toList(),
        'janelas': janelas.map((j) => j.toJson()).toList(),
        'objetos': objetos.map((o) => o.toJson()).toList(),
      };
}
