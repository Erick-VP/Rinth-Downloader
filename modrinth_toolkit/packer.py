"""
Monta a estrutura final de uma instância (mods/, config/, etc.) a partir de:
 - um .mrpack local (extrai overrides/ + baixa os arquivos do índice), ou
 - uma lista de versões resolvidas (mod avulso + suas dependências)
"""
import json
import zipfile
from pathlib import Path

from . import downloader


def unpack_local_mrpack(mrpack_path: Path, dest_root: Path) -> dict:
    """
    Extrai a pasta overrides/ de dentro do .mrpack direto pra dest_root,
    e baixa todos os arquivos listados em modrinth.index.json (client != unsupported).
    """
    with zipfile.ZipFile(mrpack_path) as z:
        index = json.loads(z.read("modrinth.index.json"))

        for name in z.namelist():
            if name.startswith("overrides/") and not name.endswith("/"):
                target = dest_root / name[len("overrides/"):]
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as src, open(target, "wb") as dst:
                    dst.write(src.read())

    entries = []
    for f in index["files"]:
        if f.get("env", {}).get("client", "required") == "unsupported":
            continue
        entries.append({
            "path": f["path"],
            "url": f["downloads"][0],
            "hashes": f.get("hashes", {}),
        })

    result = downloader.download_all(entries, dest_root)
    return {"index": index, "download_result": result}


def pack_loose_mods(resolved_versions: list[dict], dest_root: Path) -> dict:
    """
    resolved_versions: lista de {"project_id": ..., "version": {...}}
    vinda de dependency_resolver.resolve_dependencies().
    Baixa cada arquivo primário direto pra dest_root/mods/.
    """
    entries = []
    for item in resolved_versions:
        version = item["version"]
        files = version["files"]
        primary = next((f for f in files if f.get("primary")), files[0])
        entries.append({
            "path": f"mods/{primary['filename']}",
            "url": primary["url"],
            "hashes": primary.get("hashes", {}),
        })

    result = downloader.download_all(entries, dest_root)
    return {"download_result": result}
