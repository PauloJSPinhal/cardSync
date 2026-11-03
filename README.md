# cardSync

**Gestor de arquivo e partilha fotográfica no Google Drive** — aplicação Flutter multiplataforma (Android, iOS, Linux, macOS, Windows, Web).

A aplicação automatiza a ingestão, triagem, arquivo rigoroso e partilha seletiva de reportagens fotográficas, respeitando a especificação em [`Especificacoes_tecnicas.md`](Especificacoes_tecnicas.md).

## Funcionalidades

- Nomenclatura padronizada de pastas: `yyyymmdd_evento_local`
- Apresentação visual: `DD/MM/AAAA — Evento, Local`
- Hierarquia interna: `01_RAW`, `02_JPG_Original`, `03_Tratadas`, `04_Docs`
- Triagem por extensão (RAW: `.cr2`/`.cr3`/`.dng`; JPG: `.jpg`/`.jpeg`)
- Deduplicação por hash MD5
- Manifesto JSON por coleção
- Partilha restrita à subpasta `03_Tratadas` (permissão `reader`)
- Código QR com o link da pasta
- Google Sign-In (Android/iOS) e OAuth2 desktop (Linux/macOS/Windows)

## Documentação

| Ficheiro | Conteúdo |
|---|---|
| [`README.md`](README.md) | Visão geral |
| [`docs/SETUP.md`](docs/SETUP.md) | Instalação e configuração do ambiente |
| [`docs/USAGE.md`](docs/USAGE.md) | Guia de utilização da aplicação |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Arquitetura e estrutura do código |
| [`docs/API.md`](docs/API.md) | Serviços e integração com a Google Drive API |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Histórico de versões |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Guia de contribuição |

## Execução rápida

```bash
flutter pub get
flutter run -d linux      # ou -d <device_id>
flutter build apk         # Android
flutter build linux       # binário Linux
```

## Licença

MIT.
