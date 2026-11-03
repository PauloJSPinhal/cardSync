"""GUI GTK3 do cardSync."""

import os
import threading
import json
from datetime import date

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf

from ..core.config import load_config, save_config, get_backend
from ..core.naming import display_title
from ..core.importer import group_files, list_supported
from ..core.collection import create_collection, upload_files, save_manifest_remote, freeze_collection
from ..core.exif import read_exif
from ..core.share import (share_folder_with_emails, folder_link,
                          generate_qr_bytes, email_html, email_subject, whatsapp_message)
from ..core.manifest import load_manifest

APP_NAME = "cardSync"
CONFIG_DIR = os.path.expanduser("~/.config/cardsync")
COLLECTIONS_INDEX = os.path.expanduser("~/.local/share/cardsync/collections.json")


def _load_collections():
    if os.path.exists(COLLECTIONS_INDEX):
        try:
            with open(COLLECTIONS_INDEX, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_collections(items):
    os.makedirs(os.path.dirname(COLLECTIONS_INDEX), exist_ok=True)
    with open(COLLECTIONS_INDEX, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


class CardSyncWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(title=APP_NAME, application=app)
        self.set_default_size(980, 640)
        self.cfg = load_config()
        self.backend = get_backend(self.cfg)
        self.current_manifest = None
        self.current_manifest_path = None

        # Notebook
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self._build_tab_inicio()
        self._build_tab_nova()
        self._build_tab_importar()
        self._build_tab_partilhar()
        self._build_tab_config()

        self.show_all()

    # ---------- Tab: Início ----------
    def _build_tab_inicio(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)
        lbl = Gtk.Label(label="Coleções criadas")
        lbl.set_halign(Gtk.Align.START)
        box.pack_start(lbl, False, False, 0)

        self.col_store = Gtk.ListStore(str, str, str)  # root_name, display, manifest_path
        tree = Gtk.TreeView(model=self.col_store)
        for i, title in enumerate(["Pasta", "Título", "Manifest"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            tree.append_column(col)
        scroll = Gtk.ScrolledWindow()
        scroll.add(tree)
        box.pack_start(scroll, True, True, 0)

        btnbox = Gtk.Box(spacing=6)
        btn_refresh = Gtk.Button(label="Atualizar")
        btn_refresh.connect("clicked", lambda *_: self._refresh_collections())
        btnbox.pack_start(btn_refresh, False, False, 0)
        box.pack_start(btnbox, False, False, 0)

        self.notebook.append_page(box, Gtk.Label(label="Início"))
        self._refresh_collections()

    def _refresh_collections(self):
        self.col_store.clear()
        for item in _load_collections():
            self.col_store.append([item.get("root_name", ""), item.get("display_title", ""), item.get("manifest_path", "")])

    # ---------- Tab: Nova Coleção ----------
    def _build_tab_nova(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(12)

        grid = Gtk.Grid(row_spacing=8, column_spacing=8)
        box.pack_start(grid, False, False, 0)

        grid.attach(Gtk.Label(label="Data (yyyymmdd):"), 0, 0, 1, 1)
        self.entry_date = Gtk.Entry()
        self.entry_date.set_text(date.today().strftime("%Y%m%d"))
        grid.attach(self.entry_date, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Evento:"), 0, 1, 1, 1)
        self.entry_event = Gtk.Entry()
        grid.attach(self.entry_event, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Local:"), 0, 2, 1, 1)
        self.entry_location = Gtk.Entry()
        grid.attach(self.entry_location, 1, 2, 1, 1)

        btn = Gtk.Button(label="Criar Coleção")
        btn.connect("clicked", self._on_create_collection)
        box.pack_start(btn, False, False, 0)

        self.lbl_nova_status = Gtk.Label(label="")
        self.lbl_nova_status.set_halign(Gtk.Align.START)
        box.pack_start(self.lbl_nova_status, False, False, 0)

        self.notebook.append_page(box, Gtk.Label(label="Nova Coleção"))

    def _on_create_collection(self, *_):
        d = self.entry_date.get_text().strip()
        ev = self.entry_event.get_text().strip()
        loc = self.entry_location.get_text().strip()
        if not ev or not loc:
            self.lbl_nova_status.set_text("Preencha evento e local.")
            return
        self.lbl_nova_status.set_text("A criar...")
        threading.Thread(target=self._create_collection_worker, args=(d, ev, loc), daemon=True).start()

    def _create_collection_worker(self, d, ev, loc):
        try:
            self.backend.authenticate()
            col = create_collection(self.backend, d, ev, loc)
            manifest = col["manifest"]
            save_manifest_remote(self.backend, manifest)
            # guardar manifest local
            mdir = os.path.expanduser("~/.local/share/cardsync/manifests")
            os.makedirs(mdir, exist_ok=True)
            mpath = os.path.join(mdir, col["root_name"] + ".json")
            import json
            with open(mpath, "w") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            # index
            items = _load_collections()
            items.append({"root_name": col["root_name"], "display_title": manifest["display_title"],
                          "manifest_path": mpath})
            _save_collections(items)
            GLib.idle_add(self._create_collection_done, col["root_name"], mpath, None)
        except Exception as e:
            GLib.idle_add(self._create_collection_done, None, None, str(e))

    def _create_collection_done(self, root_name, mpath, err):
        if err:
            self.lbl_nova_status.set_text(f"Erro: {err}")
        else:
            self.lbl_nova_status.set_text(f"Coleção criada: {root_name}\nManifest: {mpath}")
            self.current_manifest_path = mpath
            self._refresh_collections()
        return False

    # ---------- Tab: Importar ----------
    def _build_tab_importar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)

        # manifest selector
        hbox = Gtk.Box(spacing=6)
        hbox.pack_start(Gtk.Label(label="Manifest:"), False, False, 0)
        self.entry_manifest_import = Gtk.Entry()
        hbox.pack_start(self.entry_manifest_import, True, True, 0)
        btn_browse_m = Gtk.Button(label="...")
        btn_browse_m.connect("clicked", self._browse_manifest_import)
        hbox.pack_start(btn_browse_m, False, False, 0)
        box.pack_start(hbox, False, False, 0)

        # paths
        hbox2 = Gtk.Box(spacing=6)
        hbox2.pack_start(Gtk.Label(label="Ficheiros/Pastas:"), False, False, 0)
        self.entry_paths = Gtk.Entry()
        hbox2.pack_start(self.entry_paths, True, True, 0)
        btn_browse_f = Gtk.Button(label="Selecionar")
        btn_browse_f.connect("clicked", self._browse_files)
        hbox2.pack_start(btn_browse_f, False, False, 0)
        box.pack_start(hbox2, False, False, 0)

        # options
        optbox = Gtk.Box(spacing=12)
        self.chk_treated = Gtk.CheckButton(label="Fotos tratadas (03_Tratadas)")
        optbox.pack_start(self.chk_treated, False, False, 0)
        self.chk_dedup = Gtk.CheckButton(label="Deduplicar (MD5)")
        self.chk_dedup.set_active(True)
        optbox.pack_start(self.chk_dedup, False, False, 0)
        box.pack_start(optbox, False, False, 0)

        btn = Gtk.Button(label="Importar / Enviar")
        btn.connect("clicked", self._on_import)
        box.pack_start(btn, False, False, 0)

        self.progress = Gtk.ProgressBar()
        box.pack_start(self.progress, False, False, 0)

        self.txt_import_log = Gtk.TextView()
        self.txt_import_log.set_editable(False)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.txt_import_log)
        box.pack_start(scroll, True, True, 0)

        self.notebook.append_page(box, Gtk.Label(label="Importar"))

    def _browse_manifest_import(self, *_):
        dlg = Gtk.FileChooserDialog(title="Selecionar manifest", parent=self,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if dlg.run() == Gtk.ResponseType.OK:
            self.entry_manifest_import.set_text(dlg.get_filename())
        dlg.destroy()

    def _browse_files(self, *_):
        dlg = Gtk.FileChooserDialog(title="Selecionar ficheiros/pastas", parent=self,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        # permitir múltiplos? folder only; também oferecer ficheiros via outro botão simples
        if dlg.run() == Gtk.ResponseType.OK:
            self.entry_paths.set_text(dlg.get_filename())
        dlg.destroy()

    def _log_import(self, text):
        buf = self.txt_import_log.get_buffer()
        end = buf.get_end_iter()
        buf.insert(end, text + "\n")
        # scroll
        vadj = self.txt_import_log.get_parent().get_vadjustment()
        vadj.set_value(vadj.get_upper())

    def _on_import(self, *_):
        mpath = self.entry_manifest_import.get_text().strip()
        paths_text = self.entry_paths.get_text().strip()
        if not mpath or not paths_text:
            self._log_import("Preencha manifest e caminho.")
            return
        if not os.path.exists(mpath):
            self._log_import("Manifest não encontrado.")
            return
        paths = [p.strip() for p in paths_text.split(",") if p.strip()]
        # expandir diretórios
        files = []
        for p in paths:
            if os.path.isdir(p):
                for root, _, fs in os.walk(p):
                    for fn in fs:
                        files.append(os.path.join(root, fn))
            else:
                files.append(p)
        files = list_supported(files)
        treated = self.chk_treated.get_active()
        dedup = self.chk_dedup.get_active()
        self._log_import(f"Ficheiros suportados: {len(files)}")
        self.progress.set_fraction(0.0)
        threading.Thread(target=self._import_worker, args=(mpath, files, treated, dedup), daemon=True).start()

    def _import_worker(self, mpath, files, treated, dedup):
        try:
            self.backend.authenticate()
            ev = "Evento"
            loc = "Local"
            if mpath and os.path.exists(mpath):
                import json
                with open(mpath, "r") as f:
                    manifest = json.load(f)
                root_name = manifest.get("folder_name", "")
                parts = root_name.split("_", 2)
                if len(parts) >= 3:
                    ev = parts[1]
                    loc = parts[2]
            grouped = group_files(files, ev, loc, target_date=None, treated=treated)

            def progress_cb(fname, done, total):
                frac = done / total if total else 1.0
                GLib.idle_add(self._import_progress, frac, fname)

            mdir = os.path.expanduser("~/.local/share/cardsync/manifests")
            os.makedirs(mdir, exist_ok=True)
            total_res = {"total": 0, "uploaded": 0, "skipped": 0}
            last_mpath = mpath
            for root, subs in grouped.items():
                root_date = root.split("_", 1)[0]
                col = create_collection(self.backend, root_date, ev, loc)
                man = col["manifest"]
                sub_grouped = {root: subs}
                res = upload_files(self.backend, man, sub_grouped, progress_cb=progress_cb, dedup=dedup)
                save_manifest_remote(self.backend, man)
                mp = os.path.join(mdir, col["root_name"] + ".json")
                with open(mp, "w") as f:
                    json.dump(man, f, indent=2, ensure_ascii=False)
                last_mpath = mp
                for k in total_res:
                    total_res[k] += res[k]
            self.current_manifest_path = last_mpath
            GLib.idle_add(self._import_done, total_res, None)
        except Exception as e:
            GLib.idle_add(self._import_done, None, str(e))

    def _import_progress(self, frac, fname):
        self.progress.set_fraction(frac)
        self.progress.set_text(fname)
        return False

    def _import_done(self, res, err):
        if err:
            self._log_import(f"Erro: {err}")
        else:
            self._log_import(f"Concluído: total={res['total']} enviados={res['uploaded']} ignorados={res['skipped']}")
        self.progress.set_fraction(1.0)
        return False

    # ---------- Tab: Partilhar ----------
    def _build_tab_partilhar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)

        hbox = Gtk.Box(spacing=6)
        hbox.pack_start(Gtk.Label(label="Manifest:"), False, False, 0)
        self.entry_manifest_share = Gtk.Entry()
        hbox.pack_start(self.entry_manifest_share, True, True, 0)
        btn = Gtk.Button(label="...")
        btn.connect("clicked", self._browse_manifest_share)
        hbox.pack_start(btn, False, False, 0)
        box.pack_start(hbox, False, False, 0)

        hbox2 = Gtk.Box(spacing=6)
        hbox2.pack_start(Gtk.Label(label="E-mails (vírgula):"), False, False, 0)
        self.entry_emails = Gtk.Entry()
        hbox2.pack_start(self.entry_emails, True, True, 0)
        box.pack_start(hbox2, False, False, 0)

        btnbox = Gtk.Box(spacing=6)
        btn_share = Gtk.Button(label="Partilhar (permissões)")
        btn_share.connect("clicked", self._on_share)
        btnbox.pack_start(btn_share, False, False, 0)
        btn_qr = Gtk.Button(label="Gerar QR")
        btn_qr.connect("clicked", self._on_qr)
        btnbox.pack_start(btn_qr, False, False, 0)
        btn_wa = Gtk.Button(label="WhatsApp")
        btn_wa.connect("clicked", self._on_wa)
        btnbox.pack_start(btn_wa, False, False, 0)
        btn_email = Gtk.Button(label="Gerar E-mail HTML")
        btn_email.connect("clicked", self._on_email)
        btnbox.pack_start(btn_email, False, False, 0)
        btn_freeze = Gtk.Button(label="Congelar Coleção")
        btn_freeze.connect("clicked", self._on_freeze)
        btnbox.pack_start(btn_freeze, False, False, 0)
        box.pack_start(btnbox, False, False, 0)

        # QR image
        self.qr_image = Gtk.Image()
        box.pack_start(self.qr_image, False, False, 0)

        self.txt_share_log = Gtk.TextView()
        self.txt_share_log.set_editable(False)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.txt_share_log)
        box.pack_start(scroll, True, True, 0)

        self.notebook.append_page(box, Gtk.Label(label="Partilhar"))

    def _browse_manifest_share(self, *_):
        dlg = Gtk.FileChooserDialog(title="Selecionar manifest", parent=self,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        if dlg.run() == Gtk.ResponseType.OK:
            self.entry_manifest_share.set_text(dlg.get_filename())
        dlg.destroy()

    def _log_share(self, text):
        buf = self.txt_share_log.get_buffer()
        end = buf.get_end_iter()
        buf.insert(end, text + "\n")

    def _load_manifest_share(self):
        mpath = self.entry_manifest_share.get_text().strip()
        if not os.path.exists(mpath):
            self._log_share("Manifest não encontrado.")
            return None, None
        import json
        with open(mpath) as f:
            manifest = json.load(f)
        return manifest, mpath

    def _on_share(self, *_):
        manifest, _ = self._load_manifest_share()
        if not manifest:
            return
        emails = [e.strip() for e in self.entry_emails.get_text().split(",") if e.strip()]
        treated_id = manifest["drive_ids"]["treated_folder_id"]
        threading.Thread(target=self._share_worker, args=(treated_id, emails), daemon=True).start()

    def _share_worker(self, treated_id, emails):
        try:
            self.backend.authenticate()
            res = share_folder_with_emails(self.backend, treated_id, emails)
            url = folder_link(self.backend, treated_id)
            GLib.idle_add(self._share_done, res, url, None)
        except Exception as e:
            GLib.idle_add(self._share_done, None, None, str(e))

    def _share_done(self, res, url, err):
        if err:
            self._log_share(f"Erro: {err}")
        else:
            for r in res:
                self._log_share(f"{r['email']}: {'OK' if r['ok'] else 'ERRO ' + r.get('error','')}")
            self._log_share(f"Link: {url}")
        return False

    def _on_qr(self, *_):
        manifest, _ = self._load_manifest_share()
        if not manifest:
            return
        treated_id = manifest["drive_ids"]["treated_folder_id"]
        self.backend.authenticate()
        url = folder_link(self.backend, treated_id)
        data = generate_qr_bytes(url)
        if data:
            loader = GdkPixbuf.PixbufLoader()
            loader.write(data)
            loader.close()
            pixbuf = loader.get_pixbuf()
            # scale
            scaled = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
            self.qr_image.set_from_pixbuf(scaled)
            self._log_share(f"QR gerado para {url}")
        else:
            self._log_share("qrcode não disponível.")

    def _on_wa(self, *_):
        manifest, _ = self._load_manifest_share()
        if not manifest:
            return
        treated_id = manifest["drive_ids"]["treated_folder_id"]
        self.backend.authenticate()
        url = folder_link(self.backend, treated_id)
        ev = manifest.get("display_title", "")
        msg = whatsapp_message(ev, "", url)
        self._log_share("Mensagem WhatsApp:")
        self._log_share(msg)
        # tentar abrir browser
        import webbrowser
        webbrowser.open("https://wa.me/?text=" + __import__("urllib.parse", fromlist=["quote"]).quote(msg))

    def _on_freeze(self, *_):
        manifest, mpath = self._load_manifest_share()
        if not manifest:
            return
        try:
            self.backend.authenticate()
            freeze_collection(self.backend, manifest)
            if mpath and os.path.exists(mpath):
                import json
                with open(mpath, "w") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
            self._log_share("Coleção congelada (status=frozen).")
        except Exception as e:
            self._log_share(f"Erro: {e}")

    def _on_email(self, *_):
        manifest, _ = self._load_manifest_share()
        if not manifest:
            return
        treated_id = manifest["drive_ids"]["treated_folder_id"]
        self.backend.authenticate()
        url = folder_link(self.backend, treated_id)
        # contar fotos tratadas
        try:
            files = self.backend.list_files(treated_id)
            total = len(files)
        except Exception:
            total = 0
        subject = email_subject(manifest.get("display_title", ""), "", "")
        html = email_html(manifest.get("display_title", ""), "", "", total, url, [])
        self._log_share(f"Assunto: {subject}")
        self._log_share("HTML gerado (copiar do log):")
        self._log_share(html)

    # ---------- Tab: Configurações ----------
    def _build_tab_config(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)
        grid = Gtk.Grid(row_spacing=8, column_spacing=8)
        box.pack_start(grid, False, False, 0)

        grid.attach(Gtk.Label(label="Backend (local/gdrive):"), 0, 0, 1, 1)
        self.entry_backend = Gtk.Entry()
        self.entry_backend.set_text(self.cfg.get("backend", "local"))
        grid.attach(self.entry_backend, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Pasta base local:"), 0, 1, 1, 1)
        self.entry_localbase = Gtk.Entry()
        self.entry_localbase.set_text(self.cfg.get("local_base_dir", ""))
        grid.attach(self.entry_localbase, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Client secrets (gdrive):"), 0, 2, 1, 1)
        self.entry_secrets = Gtk.Entry()
        self.entry_secrets.set_text(self.cfg.get("gdrive", {}).get("client_secrets_path", ""))
        grid.attach(self.entry_secrets, 1, 2, 1, 1)

        btn = Gtk.Button(label="Guardar")
        btn.connect("clicked", self._save_config)
        box.pack_start(btn, False, False, 0)

        btn2 = Gtk.Button(label="Testar autenticação")
        btn2.connect("clicked", self._test_auth)
        box.pack_start(btn2, False, False, 0)

        self.lbl_config_status = Gtk.Label(label="")
        box.pack_start(self.lbl_config_status, False, False, 0)

        btnq = Gtk.Button(label="Ver quota")
        btnq.connect("clicked", self._show_quota)
        box.pack_start(btnq, False, False, 0)

        self.notebook.append_page(box, Gtk.Label(label="Configurações"))

    def _save_config(self, *_):
        self.cfg["backend"] = self.entry_backend.get_text().strip()
        self.cfg["local_base_dir"] = self.entry_localbase.get_text().strip()
        self.cfg.setdefault("gdrive", {})["client_secrets_path"] = self.entry_secrets.get_text().strip()
        save_config(self.cfg)
        self.backend = get_backend(self.cfg)
        self.lbl_config_status.set_text("Configuração guardada.")

    def _test_auth(self, *_):
        try:
            ok = self.backend.authenticate()
            self.lbl_config_status.set_text(f"Autenticação: {'OK' if ok else 'FALHOU'}")
        except Exception as e:
            self.lbl_config_status.set_text(f"Erro: {e}")

    def _show_quota(self, *_):
        try:
            self.backend.authenticate()
            about = self.backend.get_about()
            self.lbl_config_status.set_text(f"Quota: usado={about.get('used')} total={about.get('total')} livre={about.get('free')}")
        except Exception as e:
            self.lbl_config_status.set_text(f"Erro: {e}")


class CardSyncApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.cardsync.app")

    def do_activate(self):
        win = CardSyncWindow(self)
        win.present()


def main():
    app = CardSyncApp()
    app.run()


if __name__ == "__main__":
    main()