"""CLI do cardSync."""

import argparse
import os
import sys
from datetime import date

from ..core.config import load_config, get_backend
from ..core.naming import folder_name, display_title
from ..core.importer import group_files, list_supported
from ..core.collection import create_collection, upload_files, save_manifest_remote, freeze_collection
from ..core.exif import read_exif
from ..core.hashing import md5_file
from ..core.manifest import load_manifest, save_manifest
from ..core.share import share_folder_with_emails, folder_link, generate_qr_png, whatsapp_message


def cmd_create(args):
    cfg = load_config()
    backend = get_backend(cfg)
    backend.authenticate()
    d = args.date or date.today().strftime("%Y%m%d")
    col = create_collection(backend, d, args.event, args.location)
    manifest = col["manifest"]
    # guardar manifest local também
    import tempfile
    # upload manifest para 04_Docs
    save_manifest_remote(backend, manifest)
    print(f"Coleção criada: {col['root_name']}")
    print(f"  IDs: {col['ids']}")
    # guardar manifest em ficheiro local se pedido
    if args.manifest_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.manifest_out)), exist_ok=True)
        with open(args.manifest_out, "w") as f:
            import json
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"  Manifest: {args.manifest_out}")


def cmd_import(args):
    cfg = load_config()
    backend = get_backend(cfg)
    backend.authenticate()
    files = []
    for path in args.paths:
        if os.path.isdir(path):
            for root, _, fs in os.walk(path):
                for fn in fs:
                    files.append(os.path.join(root, fn))
        else:
            files.append(path)
    files = list_supported(files)
    print(f"Ficheiros suportados: {len(files)}")
    d = args.date or date.today().strftime("%Y%m%d")
    treated = args.treated
    grouped = group_files(files, args.event, args.location, target_date=_parse_date(d), treated=treated)
    print("Agrupamento por pasta raiz:")
    for root, subs in grouped.items():
        print(f"  {root}")
        for sub, ps in subs.items():
            print(f"    {sub}: {len(ps)}")
    # criar uma coleção por data de disparo (pastas paralelas)
    manifests = []
    for root, subs in grouped.items():
        root_date = root.split("_", 1)[0]
        col = create_collection(backend, root_date, args.event, args.location)
        manifest = col["manifest"]
        sub_grouped = {root: subs}
        res = upload_files(backend, manifest, sub_grouped, dedup=not args.no_dedup)
        print(f"{root}: total={res['total']} enviados={res['uploaded']} ignorados={res['skipped']}")
        save_manifest_remote(backend, manifest)
        manifests.append((root, manifest))
        if args.manifest_out:
            os.makedirs(os.path.dirname(os.path.abspath(args.manifest_out)), exist_ok=True)
            import json
            base, ext = os.path.splitext(args.manifest_out)
            outp = args.manifest_out if len(grouped) == 1 else f"{base}_{root}{ext}"
            with open(outp, "w") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            print(f"  Manifest: {outp}")


def _parse_date(s):
    from datetime import datetime
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def cmd_freeze(args):
    cfg = load_config()
    backend = get_backend(cfg)
    backend.authenticate()
    # carregar manifest
    import json
    with open(args.manifest, "r") as f:
        manifest = json.load(f)
    freeze_collection(backend, manifest)
    with open(args.manifest, "w") as f:
        import json
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Coleção congelada: {manifest['folder_name']}")


def cmd_share(args):
    cfg = load_config()
    backend = get_backend(cfg)
    backend.authenticate()
    import json
    with open(args.manifest, "r") as f:
        manifest = json.load(f)
    treated_id = manifest["drive_ids"]["treated_folder_id"]
    emails = []
    if args.emails:
        emails = [e.strip() for e in args.emails.split(",")]
    res = share_folder_with_emails(backend, treated_id, emails)
    for r in res:
        print(f"  {r['email']}: {'OK' if r['ok'] else 'ERRO ' + r.get('error','')}")
    url = folder_link(backend, treated_id)
    print(f"Link: {url}")
    if args.qr:
        path = generate_qr_png(url, out_path=args.qr)
        print(f"QR: {path}")
    if args.whatsapp:
        msg = whatsapp_message(manifest.get("display_title", ""), "", url)
        print("WhatsApp:", msg)


def cmd_status(args):
    cfg = load_config()
    backend = get_backend(cfg)
    backend.authenticate()
    about = backend.get_about()
    print(f"Backend: {cfg.get('backend')}")
    print(f"Quota: usado={about.get('used')} total={about.get('total')}")


def cmd_exif(args):
    for p in args.paths:
        info = read_exif(p)
        print(p)
        print(f"  shot_date: {info.get('shot_date')}")
        print(f"  make: {info.get('make')} model: {info.get('model')}")
        print(f"  lens: {info.get('lens')} focal: {info.get('focal_length')}")
        print(f"  f/{info.get('f_number')} {info.get('exposure_time')} ISO {info.get('iso')}")
        print(f"  md5: {md5_file(p)}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cardsync", description="Gestor de arquivo fotográfico")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create", help="Criar coleção")
    p.add_argument("--date", default=None)
    p.add_argument("--event", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--manifest-out", default=None)
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("import", help="Importar ficheiros")
    p.add_argument("paths", nargs="+")
    p.add_argument("--date", default=None)
    p.add_argument("--event", required=True)
    p.add_argument("--location", required=True)
    p.add_argument("--treated", action="store_true", help="Fotos tratadas -> 03_Tratadas")
    p.add_argument("--no-dedup", action="store_true")
    p.add_argument("--manifest-out", default=None)
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("freeze", help="Congelar coleção")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("share", help="Partilhar subpasta 03_Tratadas")
    p.add_argument("--manifest", required=True)
    p.add_argument("--emails", default=None)
    p.add_argument("--qr", default=None, help="Caminho para guardar QR PNG")
    p.add_argument("--whatsapp", action="store_true")
    p.set_defaults(func=cmd_share)

    p = sub.add_parser("status", help="Estado/quota")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("exif", help="Metadados EXIF")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_exif)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()