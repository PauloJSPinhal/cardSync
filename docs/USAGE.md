# Guia de Utilização

## Arranque

```bash
cd /home/paulo/Projetos/2_Apps/cardSync
flutter run -d linux        # desktop
flutter run                 # dispositivo ligado (Android/iOS)
```

## Login

1. Tocar no ícone **Entrar** (canto superior direito).
2. No Android/iOS abre-se o seletor de conta Google.
3. No desktop abre-se o navegador para autorizar a aplicação (OAuth).
4. Após o login, a barra superior mostra o e-mail e a quota do Drive.

## Criar uma coleção

1. No ecrã **Início**, tocar em **+ Nova Coleção**.
2. Escolher a **data** (date picker), o **evento** e o **local**.
3. Tocar em **Criar Coleção**.

A pasta `yyyymmdd_evento_local` e as subpastas `01_RAW`, `02_JPG_Original`, `03_Tratadas`, `04_Docs` são criadas no Google Drive.

## Importar fotografias

1. Abrir o separador **Importar**.
2. Definir data, evento e local.
3. Ativar/desativar **"Fotos tratadas"** (envia JPG para `03_Tratadas` em vez de `02_JPG_Original`).
4. Ativar/desativar **"Deduplicar por MD5"** (ignora ficheiros já existentes).
5. Tocar em **Selecionar ficheiros** e escolher as imagens.
6. Tocar em **Importar / Enviar**.

A barra de progresso e o log mostram o estado de cada ficheiro.

## Partilhar

1. Abrir o separador **Partilhar**.
2. Inserir o **ID da pasta `03_Tratadas`** (obtido na criação).
3. Inserir o **e-mail** do contacto.
4. Tocar em **Partilhar (reader)** — concede acesso apenas de leitura.

O QR Code com o link da pasta é gerado automaticamente.

## Configurações / Quota

No separador **Config**, **Verificar autenticação / quota** mostra o espaço usado e total da conta Google Drive.

## Regras de negócio

- `.cr2`/`.cr3`/`.dng` → `01_RAW`
- `.jpg`/`.jpeg` → `02_JPG_Original` (ou `03_Tratadas` em modo "tratadas")
- Deduplicação por MD5 contra o inventário remoto da pasta de destino
- Acesso externo concedido **apenas** à subpasta `03_Tratadas` (role `reader`)
