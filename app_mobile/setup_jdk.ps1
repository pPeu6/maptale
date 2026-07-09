# Baixa e configura um JDK 17 local para o build Android do Flutter.
# Necessário porque o plugin ar_flutter_plugin_plus exige Java 17 via toolchain.

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$pastaJdk = Join-Path $raiz ".jdk"
$zipPath = Join-Path $pastaJdk "jdk-17.zip"
$url = "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse"

New-Item -ItemType Directory -Force -Path $pastaJdk | Out-Null

$jdkHome = Get-ChildItem $pastaJdk -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "jdk-17*" } |
    Select-Object -First 1

if (-not $jdkHome) {
    Write-Host "Baixando JDK 17..."
    Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
    Write-Host "Extraindo..."
    Expand-Archive -Path $zipPath -DestinationPath $pastaJdk -Force
    Remove-Item $zipPath -Force
    $jdkHome = Get-ChildItem $pastaJdk -Directory | Where-Object { $_.Name -like "jdk-17*" } | Select-Object -First 1
}

if (-not $jdkHome) {
    throw "Falha ao preparar o JDK 17 em $pastaJdk"
}

$jdkPath = $jdkHome.FullName
Write-Host "JDK 17 pronto em: $jdkPath"

# Limpa download travado do Gradle (se existir)
$gradleJdks = Join-Path $env:USERPROFILE ".gradle\jdks"
Get-ChildItem $gradleJdks -Filter "*.lock" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem $gradleJdks -Filter "*.part" -ErrorAction SilentlyContinue | Remove-Item -Force

$gradleProps = Join-Path $raiz "android\gradle.properties"
$escaped = ($jdkPath -replace "\\", "\\\\")
$conteudo = Get-Content $gradleProps -Raw
if ($conteudo -match "org\.gradle\.java\.home=.*") {
    $conteudo = $conteudo -replace "org\.gradle\.java\.home=.*", "org.gradle.java.home=$escaped"
} else {
    $conteudo += "`norg.gradle.java.home=$escaped"
}
if ($conteudo -notmatch "org\.gradle\.java\.installations\.auto-download=false") {
    $conteudo += "`norg.gradle.java.installations.auto-download=false"
}
Set-Content -Path $gradleProps -Value $conteudo.TrimEnd() -NoNewline

$env:JAVA_HOME = $jdkPath
flutter config --jdk-dir="$jdkPath" | Out-Null

Write-Host "Configuracao concluida. Rode: flutter run"
