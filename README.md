# cardSync — Gestor de Arquivo e Partilha Fotográfica no Google Drive

Aplicação multiplataforma (Desktop prioritário, Android planeado) destinada à ingestão, triagem, arquivo rigoroso e partilha seletiva de reportagens fotográficas no Google Drive.

Automatiza:
1. Nomenclatura e estrutura padronizada de diretórios.
2. Separação física de ficheiros RAW (`.CR2`/`.CR3`/`.DNG`) e `.JPG`.
3. Divisão cronológica automática através de metadados EXIF (`DateTimeOriginal`).
4. Deduplicação inteligente por hash MD5 («Atualizar Coleção»).
5. Partilha segura com contactos/grupos (restrita à subpasta `03_Tratadas`).
6. Opções rápidas de divulgação (WhatsApp, Código QR, E-mail com miniaturas).

---

## Índice

- [Nomenclatura e Arquitetura de Pastas](#nomenclatura-e-arquitetura-de-pastas)
- [Instalação](#instalação)
- [Executar](#executar)
- [CLI](#cli)
- [GUI](#gui)
- [Configuração](#configuração)
- [Testes](#testes)
- [Estrutura do Projeto](#estrutura-do-projeto)

---

## Nomenclatura e Arquitetura de Pastas

### Regra de nomenclatura no armazenamento

```
pasta_raiz = yyyymmdd + "_" + evento + "_" + local
```

- `yyyymmdd`: ano (4 dígitos), mês (2), dia (2).
- `evento`: nome do evento sanitizado (espaços → `-`, caracteres especiais removidos).
- `local`: freguesia/concelho/localidade sanitizada.

Exemplo real: `20261103_Feira-Gandarola_Febres`

### Apresentação visual na interface (norma portuguesa)

```
Título Visível = DD/MM/AAAA — Evento, Local
```

Exemplo: `03/11/2026 — Feira-Gandarola, Febres`

### Hierarquia interna de subpastas

```
yyyymmdd_evento_local/
├── 01_RAW/             # Negativos .CR2/.CR3/.DNG originais intactos
├── 02_JPG_Original/    # Ficheiros .JPG originais diretos da câmara
├── 03_Tratadas/        # Ficheiros .JPG finais editados (alvo de partilha)
└── 04_Docs/            # manifest.json, notas, relatórios
```

---

## Instalação

### Dependências do sistema (Debian/Ubuntu)

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 python3-pil
```

### Dependências Python

```bash
pip install --break-system-packages -e .
```

Ou instalar manualmente as dependências listadas em `pyproject.toml`:
`Pillow`, `exifread`, `requests`, `qrcode`, `google-api-python-client`, `google-auth`, `google-auth-oauthlib`.

### Instalar comandos no PATH

```bash
pip install --break-system-packages -e .
```

Isto regista dois comandos: `cardsync` (CLI) e `cardsync-gui` (GTK).

---

## Executar

### Interface gráfica

```bash
cardsync-gui
```

Ou, a partir da pasta do projeto:

```bash
cd /home/paulo/Projetos/2_Apps/cardSync
python3 -m cardsync.gui.main
```

### Linha de comandos

```bash
cardsync status
```

---

## CLI

```bash
# Criar coleção
cardsync create --date 20261103 --event "Feira Gandarola" --location Febres --manifest-out m.json

# Importar ficheiros/pastas (deduplicação MD5 ativa por defeito)
cardsync import ./fotos --date 20261103 --event "Feira Gandarola" --location Febres
cardsync import ./fotos --treated   # fotos tratadas -> 03_Tratadas
cardsync import ./fotos --no-dedup  # desativar deduplicação

# Congelar coleção (arquivo frio)
cardsync freeze --manifest m.json

# Partilhar subpasta 03_Tratadas
cardsync share --manifest m.json --emails "a@b.pt,c@d.pt" --qr qr.png --whatsapp

# Estado / quota da conta
cardsync status

# Metadados EXIF
cardsync exif foto.CR2 foto.jpg
```

---

## GUI

Abas disponíveis:

- **Início** — lista de coleções criadas.
- **Nova Coleção** — formulário (data, evento, local) e criação.
- **Importar** — seleção de ficheiros/pastas, opções (tratadas, deduplicar), barra de progresso e log.
- **Partilhar** — permissões por e-mail, geração de QR Code, WhatsApp, e-mail HTML, congelar coleção.
- **Configurações** — backend (`local`/`gdrive`), pasta base local, client secrets, teste de autenticação, quota.

---

## Configuração

Ficheiro: `~/.config/cardsync/config.json`

```json
{
  "version": 1,
  "backend": "local",
  "local_base_dir": "~/.local/share/cardsync/drive",
  "gdrive": {
    "client_secrets_path": ""
  },
  "wifi_only_raw": true,
  "raw_concurrency": 4
}
```

- `backend`: `local` (filesystem) ou `gdrive` (Google Drive API v3).
- Para Google Drive: preencher `gdrive.client_secrets_path` com o caminho para o `client_secrets.json` OAuth2 e autenticar (botão "Testar autenticação" na GUI ou `cardsync status`).

Dados da aplicação:
- `~/.config/cardsync/config.json`
- `~/.local/share/cardsync/drive/` — armazenamento local (backend local)
- `~/.local/share/cardsync/manifests/` — cópias locais dos manifestos
- `~/.local/share/cardsync/collections.json` — índice de coleções

---

## Regras de negócio implementadas

- **Triagem por extensão:** `.cr2`/`.cr3`/`.dng` → `01_RAW`; `.jpg`/`.jpeg` → `02_JPG_Original` (ou `03_Tratadas` no fluxo «Adicionar Fotos Tratadas»).
- **Separação por data de captura:** análise de `DateTimeOriginal`; fotos de dias diferentes geram pastas raiz paralelas (`20261102_...`, `20261103_...`), cada uma com a estrutura interna completa.
- **Deduplicação MD5:** compara o MD5 local com o inventário remoto da pasta de destino; ficheiros já existentes são ignorados.
- **Congelar coleção:** marca `"status": "frozen"` no `manifest.json` e impede uploads acidentais na UI.
- **Partilha restrita:** acesso externo concedido apenas à subpasta `03_Tratadas` (role `reader`).
- **Canais de partilha:** WhatsApp (mensagem pré-formatada), Código QR (PNG), E-mail HTML com miniaturas e botão CTA.

---

## Manifesto (`04_Docs/manifest.json`)

Cada coleção mantém um manifesto JSON com `project_id`, `folder_name`, `display_title`, `status`, `drive_ids`, `shared_with` e `files_manifest` (nome, tipo, tamanho, MD5, data de captura, data de upload).

---

## Testes

```bash
cd /home/paulo/Projetos/2_Apps/cardSync
python3 -m unittest discover -s tests
```

14 testes cobrindo nomenclatura, importação/triagem, manifesto e backend local.

---

## Estrutura do Projeto

```
cardSync/
├── pyproject.toml
├── README.md
├── Especificacoes_tecnicas.md
├── cardsync/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core/
│   │   ├── config.py
│   │   ├── naming.py
│   │   ├── exif.py
│   │   ├── hashing.py
│   │   ├── manifest.py
│   │   ├── importer.py
│   │   ├── collection.py
│   │   ├── share.py
│   │   └── backend/
│   │       ├── base.py
│   │       ├── local.py
│   │       └── gdrive.py
│   ├── cli/
│   │   └── __main__.py
│   └── gui/
│       └── main.py
└── tests/
    ├── test_naming.py
    ├── test_importer.py
    ├── test_manifest.py
    └── test_backend_local.py
```

---

## Licença

MIT.