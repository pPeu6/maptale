# Maptale - App Mobile (Flutter/AR)

App de escaneamento AR que gera o JSON do schema compartilhado (ver
[`../schema/mapa.schema.json`](../schema/mapa.schema.json)) e envia para o
jogo do Raspberry Pi.

## Estrutura

```
lib/
  main.dart                       # bootstrap + providers
  config/configuracoes_app.dart   # IP/porta do servidor, escala, larguras padrão (persistido)
  modelos/mapa_ambiente.dart      # classes que espelham o schema JSON
  servicos/
    conversor_coordenadas_ar.dart # hit-test AR -> (x, y) relativo ao 1º toque
    servico_upload.dart           # POST para /upload_map
  estado/sessao_mapeamento.dart   # estado dos modos parede/porta/janela/objeto
  telas/
    tela_inicial.dart             # pede permissão de câmera, navega para AR/config
    tela_ar.dart                  # câmera AR + detecção de plano + toques
    tela_preview.dart             # prévia 2D top-down + botão Enviar
    tela_configuracoes.dart       # IP, porta, escala, larguras padrão
  widgets/
    barra_modos.dart              # troca de modo + desfazer/novo segmento/fechar/finalizar
    seletor_tipo_objeto.dart      # dropdown de tipos de objeto
    pintor_top_down.dart          # CustomPainter (placeholders coloridos)
```

## Primeira execução

Este repositório contém apenas o código Dart (`lib/`, `pubspec.yaml`). As
pastas nativas (`android/`, `ios/`) precisam ser geradas localmente com o
Flutter instalado, pois dependem da sua toolchain (versões de SDK, etc.):

```bash
cd app_mobile
flutter create . --platforms=android,ios --org com.maptale
flutter pub get
```

Depois de gerar as pastas nativas, aplique as configurações abaixo.

### Android (`android/app/`)

- `build.gradle`: `minSdkVersion 24` (exigido pelo ARCore).
- `src/main/AndroidManifest.xml`: adicionar dentro de `<manifest>`:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-feature android:name="android.hardware.camera.ar" android:required="true" />
<meta-data android:name="com.google.ar.core" android:value="required" />
```

### iOS (`ios/`)

- `Runner/Info.plist`: adicionar `NSCameraUsageDescription` explicando o uso
  da câmera para AR.
- `Podfile`: definir `platform :ios, '15.0'` e adicionar o `post_install`
  sugerido na documentação do `ar_flutter_plugin_plus` (permissões via
  `permission_handler`):

```ruby
post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '15.0'
      config.build_settings['GCC_PREPROCESSOR_DEFINITIONS'] ||= ['$(inherited)']
      config.build_settings['GCC_PREPROCESSOR_DEFINITIONS'] << 'PERMISSION_CAMERA=1'
    end
  end
end
```

## Rodando

```bash
flutter run
```

Configure o IP do servidor Flask (rodando no Raspberry Pi, porta `5000`
por padrão) na tela de Configurações antes de enviar um mapa.

## Placeholders visuais

A prévia 2D (`pintor_top_down.dart`) usa retângulos/linhas coloridas no
lugar do tileset final. Quando os PNGs (`chao.png`, `parede.png`,
`porta.png`, `janela.png`) forem fornecidos, substitua os `canvas.drawRect`/
`drawLine` por `canvas.drawImageRect` usando os sprites carregados.
