# Especificação Técnica do Sistema: Gestor de Arquivo e Partilha Fotográfica no Google Drive

## 1. Visão Geral do Projeto

Aplicação multiplataforma (Android prioritário + Desktop/PC) destinada à ingestão, triagem, arquivo rigoroso e partilha seletiva de reportagens fotográficas no Google Drive.

A aplicação automatiza:

1. A nomenclatura e estrutura padronizada de diretórios.

2. A separação física de ficheiros RAW (`.CR2`) e `.JPG`.

3. A divisão cronológica automática através de metadados EXIF (`DateTimeOriginal`).

4. A deduplicação inteligente por hash MD5 («Atualizar Coleção»).

5. A partilha segura com contactos/grupos (restrita exclusivamente à subpasta de fotografias tratadas).

6. Opções rápidas de divulgação (WhatsApp, Código QR dinâmico e E-mail com miniaturas).

## 2. Nomenclatura e Arquitetura de Pastas

### 2.1. Regra de Nomenclatura no Armazenamento (Google Drive)

Cada coleção principal de fotografias recebe um identificador estrito de pasta:

$$
\text{pasta\_raiz} = \text{yyyymmdd} + \text{"\_"} + \text{evento} + \text{"\_"} + \text{local}
$$

* `yyyymmdd`: Ano com 4 dígitos, mês com 2 dígitos, dia com 2 dígitos (ex.: `20261103`).

* `evento`: Nome do evento ou sessão sanitizado (espaços convertidos em hífen `-`, caracteres especiais removidos).

* `local`: Freguesia, concelho ou localidade sanitizada (ex.: `Febres`, `Cantanhede`).

* **Exemplo real:** `20261103_Feira-Gandarola_Febres`

### 2.2. Apresentação Visual na Interface (Norma Portuguesa)

A interface de utilizador (UI) deve converter a representação da data para a norma portuguesa:

$$
\text{Título Visível} = \text{DD/MM/AAAA — Evento, Local}
$$

* **Exemplo:** `03/11/2026 — Feira-Gandarola, Febres`

### 2.3. Hierarquia Interna de Subpastas

Dentro de cada pasta raiz criada no Google Drive, o sistema gera a seguinte árvore:

```
yyyymmdd_evento_local/
├── 01_RAW/             # Negativos .CR2 originais intactos
├── 02_JPG_Original/    # Ficheiros .JPG originais diretos da câmara
├── 03_Tratadas/        # Ficheiros .JPG finais editados/exportados (alvo de partilha)
└── 04_Docs/            # manifest.json, notas, relatórios e documentos

```

## 3. Regras de Negócio e Lógica Operacional

### 3.1. Entrada de Dados Prévios

Antes de iniciar qualquer transferência ou atualização, o ecrã solicita três parâmetros:

1. **Data do Projeto:** Pré-preenchida com a data do sistema atual (`yyyymmdd`), mas com seletor de calendário/edição manual ativo para permitir criação ou atualização de trabalhos de datas passadas.

2. **Evento:** Texto livre (sanitizado na submissão).

3. **Local:** Texto livre (sanitizado na submissão).

### 3.2. Triagem e Separação Automática por Extensão

O motor de processamento inspeciona a extensão de cada ficheiro:

* Se `file.extension` $\in \{\text{"cr2"}, \text{"cr3"}, \text{"dng"}\}$ $\rightarrow$ Destino: `01_RAW/`

* Se `file.extension` $\in \{\text{"jpg"}, \text{"jpeg"}\}$:

  * No fluxo regular de importação: Destino: `02_JPG_Original/`

  * No fluxo explícito de «Adicionar Fotos Tratadas»: Destino: `03_Tratadas/`

### 3.3. Separação Automática por Data de Captura (Opção 3)

Durante a validação prévia ao upload, a aplicação analisa o campo EXIF `DateTimeOriginal` de cada ficheiro:

1. Compara a data de disparo com a data definida no formulário (`targetDate`).

2. Caso surjam fotos captadas num dia diferente (ex.: evento com início às 23:00 de dia 02 e continuação a dia 03):

   * O sistema **não mistura nem bloqueia** o processo.

   * Cria automaticamente pastas paralelas no mesmo nível do Google Drive com as respetivas datas:

     * `20261102_Feira-Gandarola_Febres/`

     * `20261103_Feira-Gandarola_Febres/`

   * Cada pasta gerada herda a estrutura interna (`01_RAW`, `02_JPG_Original`, `03_Tratadas`, `04_Docs`).

### 3.4. Modo «Atualizar Coleção» (Deduplicação por Hash MD5)

1. Antes de iniciar o envio binário, a app solicita à API do Google Drive a lista de ficheiros contidos na pasta de destino, recolhendo: `name`, `size`, e `md5Checksum`.

2. A aplicação calcula localmente o MD5 dos ficheiros em fila de espera.

3. Se o MD5 local já existir no inventário remoto dessa pasta, o ficheiro é descartado do envio.

4. São transferidos estritamente os ficheiros novos ou alterados.

### 3.5. Congelar Coleção (Arquivo Frio)

Ação que finaliza o ciclo de vida da coleção:

* Valida a integridade de todos os ficheiros via MD5 entre local e remoto.

* Atualiza a chave `"status": "frozen"` no `manifest.json`.

* Limpa caches temporárias locais e miniaturas desnecessárias do armazenamento do dispositivo.

* Marca a pasta na UI com um ícone de cadeado/arquivo frio, impedindo uploads acidentais.

## 4. Partilha e Comunicação

A regra de ouro da aplicação: **O acesso externo concedido a clientes e contactos é restrito à subpasta `03_Tratadas`**. As pastas `01_RAW` e `02_JPG_Original` permanecem privadas.

### 4.1. Permissões na Google Drive API

* **Endpoint:** `POST https://www.googleapis.com/drive/v3/files/{fileId}/permissions`

* **Target FileId:** ID exclusivo da subpasta `03_Tratadas`.

* **Role:** `reader` (apenas visualização/download; sem permissão de edição ou eliminação).

* **Type:** `user` (para endereços de e-mail específicos).

### 4.2. Integração com Contactos e Grupos

* **Android:**

  * Seleção individual via `Intent(Intent.ACTION_PICK, ContactsContract.Contacts.CONTENT_URI)`.

  * Grupos de contactos resolvidos via **Google People API** (`contactGroups`), expandindo as etiquetas para os e-mails dos membros correspondentes.

* **Desktop:** Leitura via Google People API autenticada.

### 4.3. Canais de Partilha

#### A. WhatsApp / Mensagens de Texto

A aplicação compõe e abre a intent com mensagem pronta:

```
Olá! As fotos tratadas de Feira-Gandarola, Febres já estão disponíveis:
https://drive.google.com/drive/folders/{id_pasta_03_Tratadas}

```

#### B. Código QR no Ecrã

* Gera dinamicamente um código QR com o URL web direto da subpasta `03_Tratadas`.

* Exibido em modal no telemóvel para leitura direta pela câmara de outras pessoas em campo.

#### C. E-mail com Miniaturas de Destaque

Para coleções com 100 ou mais fotos, não se anexam todos os ficheiros. O fluxo de e-mail opera assim:

1. A app seleciona por defeito as primeiras 3 a 5 fotos da subpasta `03_Tratadas` (permitindo substituição rápida pelo utilizador).

2. As fotos selecionadas são redimensionadas para miniaturas leves (< 150 KB cada).

3. O e-mail é gerado em HTML:

   * **Assunto:** `Fotos disponíveis: [Evento], [Local] ([DD/MM/AAAA])`

   * **Corpo:** Texto de boas-vindas, grelha com as miniaturas embebidas e botão de ação (*CTA*) com link para a pasta completa no Drive:

     ```
     <p>Olá,</p>
     <p>As fotografias tratadas de <strong>Feira Gandarola</strong> em <strong>Febres</strong> já se encontram disponíveis.</p>
     <div style="display: flex; gap: 8px;">
       <!-- Imagens de miniatura embebidas -->
     </div>
     <p style="margin-top: 16px;">
       <a href="https://drive.google.com/drive/folders/{id_pasta_03_Tratadas}" 
          style="background-color: #1a73e8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
          Ver Álbum Completo (142 Fotografias)
       </a>
     </p>
     
     ```

## 5. Inspeção, Filtros e Infraestrutura

### 5.1. Painel de Metadados EXIF

Ao visualizar qualquer fotografia dentro da app, apresentar:

* Equipamento: Marca e Modelo da Câmara.

* Objetiva: Modelo e Distância Focal utilizada.

* Exposição: Abertura ($f$-stop), Velocidade do Obturador ($1/x\text{s}$), Sensibilidade ISO.

* Data e Hora original do disparo (`DateTimeOriginal`).

### 5.2. Filtros e Pesquisa Rápida na App

Barra de filtros de acesso instantâneo:

* Por Ano (ex.: `2026`).

* Por Localidade (ex.: `Febres`).

* Por Termo do Evento (ex.: `Gandarola`).

### 5.3. Restrições de Rede e Quota

* **Opção «Carregar RAW Apenas por Wi-Fi»:** Ativada por defeito. Se a ligação for rede móvel (celular), a transferência de `.CR2` fica em fila de espera pausada; ficheiros `.JPG` podem ter permissão independente.

* **Barra de Quota da Conta:** Consulta periódica à API (`About.get`) para expor espaço utilizado e restante da conta Google Drive ativa.

## 6. Esquema do Ficheiro de Manifesto Local/Remoto

Cada coleção mantém na pasta `04_Docs/manifest.json` o seguinte registo em JSON:

```
{
  "schema_version": "1.0",
  "project_id": "proj_20261103_feira_gandarola",
  "folder_name": "20261103_Feira-Gandarola_Febres",
  "display_title": "03/11/2026 — Feira-Gandarola, Febres",
  "status": "active",
  "created_at": "2026-11-03T02:40:00Z",
  "updated_at": "2026-11-03T02:40:00Z",
  "drive_ids": {
    "root_folder_id": "drive_root_id_xxx",
    "raw_folder_id": "drive_raw_id_xxx",
    "jpg_folder_id": "drive_jpg_id_xxx",
    "treated_folder_id": "drive_treated_id_xxx",
    "docs_folder_id": "drive_docs_id_xxx"
  },
  "shared_with": [
    {
      "email": "contacto@exemplo.pt",
      "permission_id": "perm_id_123",
      "granted_at": "2026-11-03T02:45:00Z",
      "target_folder": "03_Tratadas"
    }
  ],
  "files_manifest": [
    {
      "filename": "_MG_5021.CR2",
      "type": "RAW",
      "size_bytes": 28410290,
      "md5": "d41d8cd98f00b204e9800998ecf8427e",
      "shot_date": "2026-11-03T10:14:22Z",
      "uploaded_at": "2026-11-03T02:41:00Z"
    },
    {
      "filename": "_MG_5021.JPG",
      "type": "JPG_ORIGINAL",
      "size_bytes": 6291456,
      "md5": "098f6bcd4621d373cade4e832627b4f6",
      "shot_date": "2026-11-03T10:14:22Z",
      "uploaded_at": "2026-11-03T02:41:00Z"
    }
  ]
}

```

## 7. Requisitos de Implementação por Plataforma

### 7.1. Android

* **Compatibilidade:** Android 10+ (API Level 29+).

* **Partilha Nativa:** Registo de `IntentFilter` para receber partilhas da galeria com MIME types `image/*` e `application/octet-stream` (para `.CR2`).

* **Trabalho em Fundo:** Utilização de `WorkManager` com `ForegroundService` e notificação persistente na barra de estado para uploads pesados sem risco de terminação pelo sistema.

* **Leitura EXIF:** Biblioteca oficial `androidx.exifinterface:exifinterface`.

* **Rede:** Constraints do `WorkManager` configuradas com `NetworkType.UNMETERED` para a fila de ficheiros RAW.

### 7.2. Desktop / PC (Linux, Windows, macOS)

* **Compatibilidade:** Aplicação em Flutter Desktop ou React/Electron/Tauri.

* **Importação Direta:** Funcionalidade de arrastar e largar (*Drag and Drop*) de diretórios inteiros de cartões de memória (SD/CFexpress).

* **Concorrência:** Leitura em blocos paralelos com controlo de largura de banda e limite de concorrência HTTP para a API do Google Drive (máximo de 4 a 6 uploads simultâneos).