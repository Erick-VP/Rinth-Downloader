import json
import os
import urllib.request
import sys

INDEX_FILE = "modrinth_index.json"
OUTPUT_DIR = "mods_baixados"

def main():
    if not os.path.exists(INDEX_FILE):
        print(f"ERRO: não achei '{INDEX_FILE}' nesta pasta. Coloque-o junto com este script.")
        sys.exit(1)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Modpack: {data.get('name')} - versão {data.get('versionId')}")
    print(f"Minecraft: {data['dependencies'].get('minecraft')} | NeoForge: {data['dependencies'].get('neoforge')}")

    files = data["files"]

    to_download = [
        f for f in files
        if f.get("env", {}).get("client", "required") != "unsupported"
    ]

    print(f"Total de arquivos no índice: {len(files)}")
    print(f"Arquivos a baixar (client): {len(to_download)}\n")

    ok, fail = 0, []

    for i, entry in enumerate(to_download, 1):
        rel_path = entry["path"]
        url = entry["downloads"][0]
        dest_path = os.path.join(OUTPUT_DIR, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        if os.path.exists(dest_path) and os.path.getsize(dest_path) == entry.get("fileSize", -1):
            print(f"[{i}/{len(to_download)}] já existe, pulando: {rel_path}")
            ok += 1
            continue

        print(f"[{i}/{len(to_download)}] baixando: {rel_path}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, "wb") as out:
                out.write(resp.read())
            ok += 1
        except Exception as e:
            print(f"    FALHOU: {e}")
            fail.append((rel_path, url, str(e)))

    print("\n===== RESUMO =====")
    print(f"Baixados/OK: {ok}")
    print(f"Falharam: {len(fail)}")
    if fail:
        print("\nArquivos que falharam (baixe manualmente pelo link):")
        for path, url, err in fail:
            print(f" - {path}\n   {url}\n   erro: {err}")

    print(f"\nPronto! Os arquivos estão em: ./{OUTPUT_DIR}/mods (e outras pastas, se houver)")
    print("Copie o CONTEÚDO dessas pastas para dentro da pasta .minecraft da sua instância NeoForge no TLauncher.")

if __name__ == "__main__":
    main()
