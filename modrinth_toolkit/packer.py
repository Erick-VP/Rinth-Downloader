"""
Monta a estrutura final de uma instância (mods/, config/, etc.) a partir de:
 - um .mrpack local (extrai overrides/ + baixa os arquivos do índice), ou
 - uma lista de versões resolvidas (mod avulso + suas dependências)
"""
import json
import zipfile
from pathlib import Path

from . import downloader, logging_setup
from . import modrinth_client as api

log = logging_setup.get_logger(__name__)

# pasta de destino dentro da instância, por tipo de projeto do Modrinth
FOLDER_BY_PROJECT_TYPE = {
    "mod": "mods",
    "resourcepack": "resourcepacks",
    "shader": "shaderpacks",
    "datapack": "datapacks",
    "plugin": "plugins",
}
DEFAULT_FOLDER = "mods"


def unpack_local_mrpack(mrpack_path: Path, dest_root: Path, delete_mrpack_after: bool = False) -> dict:
    """
    Extrai a pasta overrides/ de dentro do .mrpack direto pra dest_root,
    e baixa todos os arquivos listados em modrinth.index.json (client != unsupported).

    delete_mrpack_after: use True quando o .mrpack foi baixado só como um
    passo intermediário (ex: escolhido por link) e não deve ficar jogado
    dentro da pasta final da instância. Deixe False quando for o arquivo
    original que o próprio usuário forneceu.
    """
    with zipfile.ZipFile(mrpack_path) as z:
        index = json.loads(z.read("modrinth.index.json"))
        api.check_index_format(index)

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

    if delete_mrpack_after:
        try:
            mrpack_path.unlink()
            log.debug(f"Removido arquivo temporário: {mrpack_path}")
        except OSError as e:
            log.warning(f"Não consegui remover o .mrpack temporário {mrpack_path}: {e}")

    return {"index": index, "download_result": result}


def _resolve_folders(resolved_versions: list[dict]) -> dict[str, str]:
    """
    Descobre a pasta certa (mods/resourcepacks/shaderpacks/...) pra cada
    project_id, buscando o project_type em lote (1 chamada só, não 1 por mod).
    """
    project_ids = list({item["project_id"] for item in resolved_versions})
    folder_by_project_id: dict[str, str] = {}
    try:
        projects = api.get_projects_bulk(project_ids)
        for p in projects:
            folder_by_project_id[p["id"]] = FOLDER_BY_PROJECT_TYPE.get(
                p.get("project_type", ""), DEFAULT_FOLDER
            )
    except Exception as e:  # noqa: BLE001
        log.warning(
            f"Não consegui confirmar o tipo de cada dependência ({e}); "
            f"assumindo '{DEFAULT_FOLDER}/' pra todas."
        )
    return folder_by_project_id


def pack_loose_mods(resolved_versions: list[dict], dest_root: Path) -> dict:
    """
    resolved_versions: lista de {"project_id": ..., "version": {...}}
    vinda de dependency_resolver.resolve_dependencies().
    Baixa cada arquivo primário na pasta certa (mods/resourcepacks/shaderpacks/...)
    de acordo com o tipo real do projeto, não assume tudo como "mod".
    """
    folder_by_project_id = _resolve_folders(resolved_versions)

    entries = []
    for item in resolved_versions:
        version = item["version"]
        files = version["files"]
        primary = next((f for f in files if f.get("primary")), files[0])
        folder = folder_by_project_id.get(item["project_id"], DEFAULT_FOLDER)
        entries.append({
            "path": f"{folder}/{primary['filename']}",
            "url": primary["url"],
            "hashes": primary.get("hashes", {}),
        })

    result = downloader.download_all(entries, dest_root)
    return {"download_result": result}
