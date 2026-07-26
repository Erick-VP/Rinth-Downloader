"""
Resolve recursivamente as dependências obrigatórias ('required') de uma
'version' do Modrinth. Só é necessário quando o usuário baixa um mod avulso
(modpacks fechados já vêm com tudo resolvido no modrinth.index.json).
"""
from . import modrinth_client as api


def resolve_dependencies(version: dict, loader: str, game_version: str,
    _seen: set | None = None) -> list[dict]:
    """
    Retorna uma lista de {"project_id": ..., "version": {...}} contendo a
    version original + todas as dependências obrigatórias encontradas,
    recursivamente, sem duplicatas.
    """
    if _seen is None:
        _seen = set()

    result: list[dict] = []
    version_id = version["id"]
    if version_id in _seen:
        return result
    _seen.add(version_id)

    result.append({"project_id": version["project_id"], "version": version})

    for dep in version.get("dependencies", []):
        if dep.get("dependency_type") != "required":
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
                print(
                    f"  [aviso] dependência obrigatória {dep['project_id']} não tem "
                    f"build para loader={loader}/mc={game_version}; pulando."
                )

        if dep_version:
            result.extend(resolve_dependencies(dep_version, loader, game_version, _seen))

    return result
