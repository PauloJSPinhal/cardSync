# Changelog

Todas as alterações relevantes do projeto são registadas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e o versionamento segue [SemVer](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-11-03

### Adicionado

- Projeto Flutter multiplataforma (Android, iOS, Linux, macOS, Windows, Web).
- Ecrã **Início** com estado de login e quota.
- Ecrã **Nova Coleção** com date picker e validação.
- Ecrã **Importar** com triagem por extensão e deduplicação MD5.
- Ecrã **Partilhar** com permissões `reader` e QR Code.
- Ecrã **Configurações** com verificação de autenticação/quota.
- Serviço de autenticação (Google Sign-In no mobile, OAuth2 no desktop).
- Serviço Google Drive API v3 (pastas, upload, permissões).
- Lógica de domínio: nomenclatura, importação, hashing, manifesto.
- Tema Material 3 claro/escuro.
- Documentação (`README.md` e `docs/`).

### Removido

- Versão anterior em Python (substituída pela implementação Flutter).
