"""
Download paralelo de arquivos, com:
 - verificação de integridade via hash (sha1/sha512, o que a API fornecer)
 - retry automático em caso de falha de rede
 - cache local por hash, pra não baixar de novo o que já existe no disco
"""
import hashlib
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from . import logging_setup

log = logging_setup.get_logger(__name__)

CACHE_DIR = Path.home() / ".modrinth_toolkit_cache"
CACHE_DIR.mkdir(exist_ok=True)

MAX_WORKERS = 8
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60


def _hash_file(path: Path, algo: str = "sha1") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _pick_algo(hashes: dict) -> str | None:
    if "sha1" in hashes:
        return "sha1"
    if "sha512" in hashes:
        return "sha512"
    return None


def _download_one(entry: dict, dest_root: Path) -> dict:
    """
    entry esperado:
        {"path": "mods/exemplo.jar", "url": "https://...", "hashes": {"sha1": "...", "sha512": "..."}}
    """
    rel_path = entry["path"]
    url = entry["url"]
    hashes = entry.get("hashes", {})
    dest = dest_root / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)

    algo = _pick_algo(hashes)
    cache_path = CACHE_DIR / f"{algo}-{hashes[algo]}" if algo else None

    # checa se existe no cache local (de uma execução anterior)
    if cache_path and cache_path.exists():
        shutil.copy(cache_path, dest)
        return {"path": rel_path, "status": "cache", "error": None}

    last_err = None
    for _attempt in range(1, MAX_RETRIES + 1):
        try:
            with requests.get(url, stream=True, timeout=TIMEOUT_SECONDS) as r:
                r.raise_for_status()
                with open(dest, "wb") as out:
                    shutil.copyfileobj(r.raw, out)

            if algo:
                got = _hash_file(dest, algo)
                if got.lower() != hashes[algo].lower():
                    raise ValueError(
                        f"hash não confere (esperado {hashes[algo]}, obtido {got})"
                    )
                shutil.copy(dest, cache_path)

            return {"path": rel_path, "status": "ok", "error": None}

        except Exception as e:  # noqa: BLE001 - captura qualquer falha de rede/IO
            last_err = e

    return {"path": rel_path, "status": "fail", "error": str(last_err)}


def download_all(entries: list[dict], dest_root: Path,
                max_workers: int = MAX_WORKERS) -> dict:
    """
    Baixa todos os arquivos em paralelo. Retorna:
        {"ok": [...], "cached": [...], "failed": [...]}
    """
    dest_root.mkdir(parents=True, exist_ok=True)
    ok, cached, failed = [], [], []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_download_one, e, dest_root): e for e in entries}
        total = len(futures)
        done = 0
        for fut in as_completed(futures):
            done += 1
            res = fut.result()
            log.info(f"[{done}/{total}] {res['status'].upper():6s} {res['path']}")
            if res["status"] == "fail":
                log.debug(f"Detalhe da falha em {res['path']}: {res['error']}")
            if res["status"] == "ok":
                ok.append(res)
            elif res["status"] == "cache":
                cached.append(res)
            else:
                failed.append(res)

    return {"ok": ok, "cached": cached, "failed": failed}
