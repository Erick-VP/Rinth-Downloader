"""
Cliente leve para a API pública do Modrinth (v2).
Docs oficiais: https://docs.modrinth.com/api/
"""
import json
import time

import requests

from . import logging_setup
from .rate_limiter import RateLimiter

API_BASE = "https://api.modrinth.com/v2"
USER_AGENT = "modrinth-toolkit/0.1 (uso pessoal - contato: seu-email-aqui)"

# formato de índice de .mrpack que este código sabe processar.
# se o Modrinth mudar o schema, isso avisa em vez de quebrar silenciosamente.
SUPPORTED_INDEX_FORMAT_VERSION = 1

log = logging_setup.get_logger(__name__)

# Modrinth é bem mais tolerante que a CurseForge, mas mesmo assim vale ter
# uma proteção básica: intervalo mínimo curto entre chamadas + backoff real
# se algum dia bater 429.
_rate_limiter = RateLimiter(min_interval=0.15, max_backoff=120.0)

MAX_RETRIES = 4


class ModrinthAPIError(Exception):
    """Erro genérico de comunicação com a API do Modrinth."""


def _get(endpoint: str, params: dict | None = None) -> dict | list:
    url = f"{API_BASE}{endpoint}"
    headers = {"User-Agent": USER_AGENT}

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        _rate_limiter.wait_before_call()
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        except requests.RequestException as e:
            last_err = e
            log.warning(f"Falha de rede em {url} (tentativa {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(min(2 ** attempt, 30))
            continue

        if resp.status_code == 429 or resp.status_code == 403:
            _rate_limiter.register_rate_limit_hit()
            last_err = ModrinthAPIError(f"HTTP {resp.status_code} em {url}")
            continue

        if resp.status_code != 200:
            raise ModrinthAPIError(f"GET {url} -> HTTP {resp.status_code}: {resp.text[:300]}")

        _rate_limiter.register_success()
        return resp.json()

    raise ModrinthAPIError(f"Falhou após {MAX_RETRIES} tentativas em {url}: {last_err}")


def get_project(id_or_slug: str) -> dict:
    """Retorna os metadados de um projeto (mod, modpack, resourcepack, etc)."""
    return _get(f"/project/{id_or_slug}")


def get_project_versions(id_or_slug: str, loaders: list[str] | None = None,
                        game_versions: list[str] | None = None) -> list[dict]:
    """
    Lista as versões de um projeto, já filtradas por loader e/ou versão do MC.
    A API espera os filtros como arrays serializados em JSON dentro da query string.
    Vem ordenado do mais recente pro mais antigo.
    """
    params = {}
    if loaders:
        params["loaders"] = json.dumps(loaders)
    if game_versions:
        params["game_versions"] = json.dumps(game_versions)
    return _get(f"/project/{id_or_slug}/version", params=params)


def get_version(version_id: str) -> dict:
    """Retorna os detalhes de uma versão específica (arquivos, dependências, etc)."""
    return _get(f"/version/{version_id}")


def get_versions_bulk(version_ids: list[str]) -> list[dict]:
    """Busca várias versões de uma vez (mais eficiente que chamar get_version em loop)."""
    if not version_ids:
        return []
    ids_param = json.dumps(version_ids)
    return _get("/versions", params={"ids": ids_param})


def get_projects_bulk(project_ids: list[str]) -> list[dict]:
    """Busca vários projetos de uma vez (usado pra descobrir project_type sem 1 chamada por mod)."""
    if not project_ids:
        return []
    ids_param = json.dumps(project_ids)
    return _get("/projects", params={"ids": ids_param})


def check_index_format(index: dict) -> None:
    """
    Confere se o formatVersion do modrinth.index.json é o que este código
    sabe interpretar. Se o Modrinth mudar o schema no futuro, isso avisa
    em vez de deixar o código quebrar em algum lugar aleatório mais na frente.
    """
    fmt = index.get("formatVersion")
    if fmt != SUPPORTED_INDEX_FORMAT_VERSION:
        log.warning(
            f"formatVersion do modrinth.index.json é {fmt!r}, mas este código "
            f"foi escrito pra formatVersion={SUPPORTED_INDEX_FORMAT_VERSION}. "
            f"Pode haver campos novos/renomeados não tratados aqui — "
            f"prossiga com atenção e reporte se algo quebrar."
        )
