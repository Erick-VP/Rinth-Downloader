"""
Cliente leve para a API pública do Modrinth (v2).
Docs oficiais: https://docs.modrinth.com/api/
"""
import json
import requests

API_BASE = "https://api.modrinth.com/v2"
USER_AGENT = "modrinth-toolkit/0.1 (uso pessoal - contato: seu-email-aqui)"


class ModrinthAPIError(Exception):
    """Erro genérico de comunicação com a API do Modrinth."""


def _get(endpoint: str, params: dict | None = None) -> dict | list:
    url = f"{API_BASE}{endpoint}"
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise ModrinthAPIError(f"GET {url} -> HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()


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
