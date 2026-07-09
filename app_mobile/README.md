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

No Windows, o plugin AR exige **Java 17**. Se o build falhar com
`Cannot find a Java installation ... languageVersion=17`, rode uma vez:

```powershell
powershell -ExecutionPolicy Bypass -File setup_jdk.ps1
```

O script baixa um JDK 17 local em `.jdk/` e configura o Gradle/Flutter.

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

## Emulador Android + ARCore

A documentação do ARCore pede **API 27+**, mas isso não significa que
qualquer emulador recente funciona. O ARCore no emulador só aceita imagens
**x86_64 com Google Play**, **sem tradução ARM** e **sem Page Size 16KB**.

O emulador padrão do Android Studio (API 37 + `ps16k`) aparece como
incompatível com ARCore — isso é esperado, não é bug do app.

### Emulador recomendado

Instale a imagem pelo **Android Studio** (o download via terminal costuma travar):

1. **Settings → Android SDK → SDK Platforms** → marque *Show Package Details*
2. Em **Android 13 (API 33)**, selecione **Google Play Intel x86_64 Atom System Image**
3. **Não** escolha imagens com **16 KB Page Size**
4. Apply → OK

Depois rode:

```powershell
powershell -ExecutionPolicy Bypass -File setup_emulador_ar.ps1
flutter emulators --launch Pixel_5_ARCore
flutter run -d Pixel_5_ARCore
```

**Alternativa imediata:** celular físico via USB (`flutter run` e escolha o SM A035M).

No emulador, abra **Extended controls > Camera** e defina a câmera traseira
como **VirtualScene** (cena 3D simulada para AR).

### Celular físico

Para testes reais de AR, prefira um aparelho da
[lista de dispositivos suportados pelo ARCore](https://developers.google.com/ar/devices).

## Placeholders visuais

A prévia 2D (`pintor_top_down.dart`) usa retângulos/linhas coloridas no
lugar do tileset final. Quando os PNGs (`chao.png`, `parede.png`,
`porta.png`, `janela.png`) forem fornecidos, substitua os `canvas.drawRect`/
`drawLine` por `canvas.drawImageRect` usando os sprites carregados.
