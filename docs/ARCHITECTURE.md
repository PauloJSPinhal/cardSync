# Arquitetura

## Visão geral

A aplicação é escrita em **Dart/Flutter**, com separação clara entre **UI**, **serviços** e **lógica de domínio** (`core`).

```
┌─────────────────────────────────────────────┐
│                   UI (Flutter)               │
│  screens/home_screen.dart                    │
│  screens/new_collection_screen.dart          │
│  screens/import_screen.dart                  │
│  screens/share_screen.dart                   │
│  screens/settings_screen.dart                │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                  Services                     │
│  services/auth_service.dart  (autenticação)   │
│  services/drive_service.dart (Drive API)      │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│                    Core                       │
│  core/naming.dart   (nomenclatura)            │
│  core/importer.dart (triagem/agrupamento)     │
│  core/hashing.dart  (MD5)                     │
│  core/manifest.dart (manifesto JSON)          │
└─────────────────────────────────────────────┘
```

## Estrutura de diretórios

```
lib/
├── main.dart                      # entrada, tema, MaterialApp
├── core/
│   ├── naming.dart                # folderName, displayTitle, sanitize, projectId
│   ├── importer.dart              # classify, groupFiles (extensões RAW/JPG)
│   ├── hashing.dart               # md5File, md5Bytes, fileSize
│   └── manifest.dart              # newManifest, addFileEntry, status
├── services/
│   ├── auth_service.dart          # Google Sign-In (mobile) + OAuth2 (desktop)
│   └── drive_service.dart         # DriveApi v3: pastas, ficheiros, permissões
└── screens/
    ├── home_screen.dart           # shell com NavigationBar + estado de login
    ├── new_collection_screen.dart # criação de coleção
    ├── import_screen.dart         # importação com dedup e progresso
    ├── share_screen.dart          # partilha (permissões + QR)
    └── settings_screen.dart       # autenticação/quota
```

## Princípios de design

- **Separação de responsabilidades** — `core` não depende de Flutter nem de serviços; é lógica pura e testável.
- **Singletons de serviço** — `AuthService.instance` e `DriveService.instance` centralizam estado.
- **Tema Material 3** — `ColorScheme.fromSeed`, claro/escuro automático (`ThemeMode.system`).
- **Navegação** — `NavigationBar` (bottom) com ecrãs independentes; `NewCollectionScreen` é empurrado via `Navigator`.
- **Feedback** — `SnackBar`, `LinearProgressIndicator`, estados de loading nos botões.

## Fluxos principais

### Criação de coleção

1. `NewCollectionScreen` valida o formulário.
2. `DriveService.ensureStructure(rootName)` cria/obtém a pasta raiz e subpastas.
3. Gera o `manifest.json` (via `core/manifest.dart`) e associa os `drive_ids`.
4. Persiste o nome da coleção em `shared_preferences`.

### Importação

1. `FilePicker` devolve os caminhos locais.
2. `core/importer.dart` classifica por extensão e agrupa por coleção.
3. Para cada subpasta, obtém o inventário remoto e calcula MD5 local.
4. `DriveService.uploadFile` envia apenas os ficheiros novos.

### Partilha

1. `DriveService.createPermission` aplica `role=reader` à pasta `03_Tratadas`.
2. `qr_flutter` gera o QR Code do link.
