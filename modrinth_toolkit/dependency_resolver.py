"""
Resolve recursivamente as dependências de uma 'version' do Modrinth.
Só é necessário quando o usuário baixa um mod avulso (modpacks fechados já
vêm com tudo resolvido no modrinth.index.json).
"""
from . import modrinth_client as api
from . import logging_setup

log = logging_setup.get_logger(__name__)


def resolve_dependencies(version: dict, loader: str, game_version: str,
                        include_optional: bool = False,
                        _seen: set | None = None) -> list[dict]:
    """
    Retorna uma lista de {"project_id": ..., "version": {...}} contendo a
    version original + todas as dependências encontradas recursivamente,
    sem duplicatas.

    Por padrão só segue dependências 'required'. Passe include_optional=True
    pra também baixar as 'optional' (ex: addons/compat que o mod recomenda
    mas não exige pra funcionar).
    """
    if _seen is None:
        _seen = set()

    result: list[dict] = []
    version_id = version["id"]
    if version_id in _seen:
        return result
    _seen.add(version_id)

    result.append({"project_id": version["project_id"], "version": version})

    wanted_types = {"required"} | ({"optional"} if include_optional else set())

    for dep in version.get("dependencies", []):
        dep_type = dep.get("dependency_type")
        if dep_type not in wanted_types:
            continue

        dep_version = None
        if dep.get("version_id"):
            dep_version = api.get_version(dep["version_id"])
        elif dep.get("project_id"):
            candidates = api.get_project_versions(
                dep["project_id"], loaders=[loader], game_versions=[game_version]
            )
            if candidates:
                dep_version = candidates[0]
            else:
                log.warning(
                    f"Dependência {dep_type} '{dep['project_id']}' não tem build "
                    f"para loader={loader}/mc={game_version}; pulando."
                )

        if dep_version:
            result.extend(
                resolve_dependencies(dep_version, loader, game_version, include_optional, _seen)
            )

    return result
