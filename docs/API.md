# Serviços e Integração

## AuthService (`lib/services/auth_service.dart`)

Autenticação Google, com comportamento distinto por plataforma.

| Método | Descrição |
|---|---|
| `init()` | Inicializa e restaura sessão (mobile). |
| `signIn()` | Login. No mobile usa `google_sign_in`; no desktop abre navegador via OAuth2. |
| `signOut()` | Termina a sessão. |
| `authenticatedClient()` | Devolve um `http.Client` autenticado (Bearer token) para a Drive API. |

Scopes usados: `https://www.googleapis.com/auth/drive`.

## DriveService (`lib/services/drive_service.dart`)

Cliente da **Google Drive API v3** (pacote `googleapis`).

| Método | Endpoint/Operação |
|---|---|
| `init()` | Constrói `DriveApi` com o client autenticado. |
| `about()` | `about.get` → `storageQuota` (usado/total). |
| `findFolder(name, {parentId})` | `files.list` com query de nome + mimeType pasta. |
| `createFolder(name, {parentId})` | `files.create` (mimeType `application/vnd.google-apps.folder`). |
| `ensureStructure(rootName)` | Cria/obtém raiz + `01_RAW`, `02_JPG_Original`, `03_Tratadas`, `04_Docs`. |
| `listFiles(folderId)` | Lista ficheiros (id, name, size, md5Checksum). |
| `uploadFile(localPath, folderId)` | `files.create` com `Media` (upload resumable). |
| `createPermission(fileId, email)` | `permissions.create` com `type=user`, `role=reader`. |
| `folderUrl(id)` | `https://drive.google.com/drive/folders/{id}`. |

## Core (lógica pura)

### naming.dart

- `sanitize(text)` — remove caracteres especiais, espaços → `-`.
- `formatDateYyyymmdd(date)` — `yyyyMMdd`.
- `folderName(date, event, location)` — `yyyymmdd_evento_local`.
- `displayTitle(date, event, location)` — `DD/MM/AAAA — Evento, Local`.
- `projectId(date, event)` — `proj_yyyymmdd_evento`.

### importer.dart

- `classify(path, {treated})` — devolve `01_RAW`, `02_JPG_Original` ou `03_Tratadas`.
- `groupFiles(paths, event, location, {targetDate, treated})` — agrupa por coleção e subpasta.

### hashing.dart

- `md5File(path)` — MD5 hexadecimal do ficheiro.
- `md5Bytes(bytes)` — MD5 de bytes.
- `fileSize(path)` — tamanho em bytes.

### manifest.dart

- `newManifest(...)` — estrutura inicial do manifesto.
- `addFileEntry(...)` — adiciona entrada (dedup por nome+md5).
- `setManifestStatus(...)` — `active`/`frozen`.

## Esquema do manifesto

```json
{
  "schema_version": "1.0",
  "project_id": "proj_20261103_feira_gandarola",
  "folder_name": "20261103_Feira-Gandarola_Febres",
  "display_title": "03/11/2026 — Feira-Gandarola, Febres",
  "status": "active",
  "created_at": "...",
  "updated_at": "...",
  "drive_ids": {
    "root_folder_id": "...",
    "raw_folder_id": "...",
    "jpg_folder_id": "...",
    "treated_folder_id": "...",
    "docs_folder_id": "..."
  },
  "shared_with": [],
  "files_manifest": []
}
```
