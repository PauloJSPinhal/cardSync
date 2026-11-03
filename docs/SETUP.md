# Instalação e Configuração

## Pré-requisitos

### Flutter SDK

Instalar o Flutter (canal stable):

```bash
cd ~
git clone https://github.com/flutter/flutter.git -b stable
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
flutter --version
flutter doctor
```

### Android SDK (para Android)

```bash
mkdir -p ~/Android/cmdline-tools
cd ~/Android/cmdline-tools
wget https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
unzip commandlinetools-linux-*.zip
mv cmdline-tools latest
```

Adicionar ao `~/.bashrc`:

```bash
export ANDROID_SDK_ROOT="$HOME/Android"
export ANDROID_HOME="$HOME/Android"
export PATH="$HOME/Android/cmdline-tools/latest/bin:$HOME/Android/platform-tools:$PATH"
```

Aceitar licenças e instalar componentes:

```bash
source ~/.bashrc
yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-36" "build-tools;36.0.0"
flutter config --android-sdk "$HOME/Android"
flutter doctor --android-licenses
```

> É necessário um JDK (17 ou superior) no `PATH` (ou `JAVA_HOME` definido).

### Linux desktop (Debian/Ubuntu)

```bash
sudo apt install -y clang cmake ninja-build pkg-config libgtk-3-dev
```

## Dependências do projeto

```bash
cd /home/paulo/Projetos/2_Apps/cardSync
flutter pub get
```

Principais pacotes (ver `pubspec.yaml`):

- `google_sign_in` — autenticação Google em Android/iOS
- `googleapis` + `googleapis_auth` — Google Drive API v3
- `crypto` — hash MD5
- `file_picker` — seleção de ficheiros
- `qr_flutter` — geração de QR Code
- `shared_preferences` — persistência local
- `url_launcher` — abrir navegador no fluxo OAuth desktop
- `http` — cliente HTTP

## Configuração OAuth

### Android/iOS

O `google_sign_in` utiliza a configuração padrão do projeto. Para produção, configurar o `SHA-1` e o client ID no `android/app` e `ios/Runner`.

### Desktop (Linux/macOS/Windows)

1. Criar um projeto na [Google Cloud Console](https://console.cloud.google.com/).
2. Ativar a **Google Drive API**.
3. Criar credenciais OAuth do tipo **"Desktop app"**.
4. Copiar o *Client ID* e colocar em `lib/services/auth_service.dart`:

```dart
final clientId = auth_io.ClientId(
  'SEU_CLIENT_ID.apps.googleusercontent.com',
  null,
);
```

## Verificação

```bash
flutter analyze
flutter test
flutter run -d linux
```
