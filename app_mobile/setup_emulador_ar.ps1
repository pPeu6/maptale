# Verifica/cria emulador Android compatível com ARCore.
#
# O emulador padrao do Android Studio (API 37 + Page Size 16KB) NAO funciona
# com ARCore. Use API 33, Google Play, x86_64, SEM "16 KB Page Size".

$ErrorActionPreference = "Stop"

$sdkRoot = $env:ANDROID_HOME
if (-not $sdkRoot) { $sdkRoot = "$env:LOCALAPPDATA\Android\Sdk" }

$avdmanager = Join-Path $sdkRoot "cmdline-tools\latest\bin\avdmanager.bat"
$imageId = "system-images;android-33;google_apis_playstore;x86_64"
$imageDir = Join-Path $sdkRoot "system-images\android-33\google_apis_playstore\x86_64"
$avdName = "Pixel_5_ARCore"

function Test-ImagemCompleta {
    param([string]$Dir)
    return (Test-Path (Join-Path $Dir "source.properties")) -and
           (Test-Path (Join-Path $Dir "system.img"))
}

if (-not (Test-ImagemCompleta $imageDir)) {
    Write-Host ""
    Write-Host "Imagem API 33 NAO encontrada ou download incompleto." -ForegroundColor Yellow
    Write-Host "O sdkmanager via terminal costuma travar (zip de 0 bytes)." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Instale pelo Android Studio (mais confiavel):" -ForegroundColor Cyan
    Write-Host "  1. Android Studio > Settings > Languages & Frameworks > Android SDK"
    Write-Host "  2. Aba 'SDK Platforms' > marque 'Show Package Details'"
    Write-Host "  3. Em Android 13 (Tiramisu) API 33, selecione:"
    Write-Host "     'Google Play Intel x86_64 Atom System Image'  (NAO escolha '16 KB Page Size')"
    Write-Host "  4. Apply > OK e aguarde o download terminar"
    Write-Host "  5. Rode este script novamente"
    Write-Host ""
    Write-Host "Alternativa imediata: use o celular fisico conectado via USB:"
    Write-Host "  flutter devices"
    Write-Host "  flutter run -d R9QT501EJRP"
    Write-Host ""
    exit 1
}

Write-Host "Imagem API 33 OK."

if (-not (Test-Path $avdmanager)) {
    throw "avdmanager nao encontrado. Instale Android SDK Command-line Tools pelo Android Studio."
}

$avdExists = & $avdmanager list avd 2>&1 | Select-String -SimpleMatch "Name: $avdName"
if ($avdExists) {
    Write-Host "AVD '$avdName' ja existe."
} else {
    Write-Host "Criando AVD '$avdName'..."
    echo no | & $avdmanager create avd --name $avdName --package $imageId --device "pixel_5"
}

Write-Host ""
Write-Host "Pronto. Para usar:" -ForegroundColor Green
Write-Host "  flutter emulators --launch $avdName"
Write-Host "  flutter run -d $avdName"
Write-Host ""
Write-Host "No emulador: Extended controls > Camera > Back = VirtualScene"
