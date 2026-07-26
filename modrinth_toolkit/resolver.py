"""
Resolve a entrada do usuário (link, slug, id do Modrinth, ou arquivo .mrpack
local) para um alvo concreto: um projeto + a versão escolhida, já compatível
com o loader e a versão do Minecraft pedidos.
"""
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import modrinth_client as api


@dataclass
class ResolvedTarget:
    source: str                     # "modrinth" ou "local_mrpack"
    project_id: Optional[str]
    project_name: Optional[str]
    project_type: Optional[str]     # "mod", "modpack", "resourcepack", "shader"...
    version: Optional[dict]         # objeto version cru da API (None se for arquivo local)
    local_mrpack_path: Optional[Path] = None


_URL_RE = re.compile(
    r"modrinth\.com/(?:mod|modpack|plugin|resourcepack|shader|datapack)/([^/?#]+)"
)


def extract_slug_from_url(url: str) -> str:
    """Extrai o slug de uma URL do Modrinth, tipo modrinth.com/modpack/create-plus -> create-plus."""
    m = _URL_RE.search(url)
    if not m:
        raise ValueError(f"Não consegui identificar o slug/projeto nesse link: {url}")
    return m.group(1)


def resolve_from_link_or_id(link_or_id: str, loader: str, game_version: str) -> ResolvedTarget:
    """
    Aceita um link completo do Modrinth, ou diretamente um slug/id de projeto.
    Já filtra as versões pelo loader e versão do Minecraft escolhidos e pega
    a mais recente compatível.
    """
    slug = extract_slug_from_url(link_or_id) if "modrinth.com" in link_or_id else link_or_id

    project = api.get_project(slug)
    versions = api.get_project_versions(slug, loaders=[loader], game_versions=[game_version])

    if not versions:
        raise ValueError(
            f"Nenhuma versão de '{project['title']}' encontrada para "
            f"loader={loader!r} e Minecraft={game_version!r}. "
            f"Confira se esse mod/modpack realmente suporta essa combinação."
        )

    chosen = versions[0]
    return ResolvedTarget(
        source="modrinth",
        project_id=project["id"],
        project_name=project["title"],
        project_type=project["project_type"],
        version=chosen,
    )


def resolve_from_local_file(path: str) -> ResolvedTarget:
    """Lê um .mrpack local e extrai as informações básicas (sem baixar nada ainda)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    with zipfile.ZipFile(p) as z:
        with z.open("modrinth.index.json") as f:
            index = json.load(f)

    return ResolvedTarget(
        source="local_mrpack",
        project_id=None,
        project_name=index.get("name"),
        project_type="modpack",
        version=None,
        local_mrpack_path=p,
    )
