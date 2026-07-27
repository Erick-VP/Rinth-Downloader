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


def list_compatible_versions(link_or_id: str, loader: str, game_version: str) -> tuple[dict, list[dict]]:
    """
    Retorna (project, versions) já filtrados por loader + versão do MC,
    ordenados do mais recente pro mais antigo. Não escolhe nenhuma — quem
    chama decide (CLI pode listar pro usuário, ou pegar versions[0] direto).
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
    return project, versions


def resolve_from_link_or_id(link_or_id: str, loader: str, game_version: str,
                            version_index: int = 0) -> ResolvedTarget:
    """
    Aceita um link completo do Modrinth, ou diretamente um slug/id de projeto.
    Filtra as versões pelo loader e versão do Minecraft escolhidos.
    Por padrão pega a mais recente compatível (version_index=0); passe um
    índice diferente pra escolher outra da lista retornada por
    list_compatible_versions().
    """
    project, versions = list_compatible_versions(link_or_id, loader, game_version)

    if version_index < 0 or version_index >= len(versions):
        raise IndexError(
            f"version_index={version_index} fora do range (0 a {len(versions) - 1})."
        )

    chosen = versions[version_index]
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

    api.check_index_format(index)

    return ResolvedTarget(
        source="local_mrpack",
        project_id=None,
        project_name=index.get("name"),
        project_type="modpack",
        version=None,
        local_mrpack_path=p,
    )
