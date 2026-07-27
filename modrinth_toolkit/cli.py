"""
CLI: pode rodar interativa (pergunta tudo por input()) ou não-interativa
(recebe tudo via argparse, útil pra automação/scripts/futura GUI).
"""
from pathlib import Path

from . import dependency_resolver, downloader, logging_setup, packer, resolver

log = logging_setup.get_logger(__name__)

LOADERS = ["fabric", "forge", "neoforge", "quilt"]


def ask(prompt: str, options: list[str] | None = None) -> str:
    while True:
        val = input(prompt).strip()
        if val and (not options or val in options):
            return val
        if options:
            print(f"  Opção inválida. Escolha entre: {', '.join(options)}")
        else:
            print("  Não pode ficar em branco.")


def ask_yes_no(prompt: str, default_no: bool = True) -> bool:
    suffix = " [s/N]: " if default_no else " [S/n]: "
    val = input(prompt + suffix).strip().lower()
    if not val:
        return not default_no
    return val in ("s", "sim", "y", "yes")


def _report(result: dict) -> None:
    print(
        f"\nOK: {len(result['ok'])} | "
        f"Cache: {len(result['cached'])} | "
        f"Falharam: {len(result['failed'])}"
    )
    for f in result["failed"]:
        print(f"  - {f['path']}: {f['error']}")


def _choose_version_interactively(project: dict, versions: list[dict]) -> int:
    """Mostra até 10 versões compatíveis e deixa o usuário escolher; Enter = mais recente."""
    print(f"\nVersões compatíveis de '{project['title']}' encontradas:")
    shown = versions[:10]
    for i, v in enumerate(shown):
        print(f"  [{i}] {v.get('version_number', '?')} — {v.get('name', '')} "
            f"({v.get('date_published', '')[:10]})")
    if len(versions) > 10:
        print(f"  (+{len(versions) - 10} versões mais antigas não mostradas)")

    val = input("Escolha o número (Enter = mais recente, [0]): ").strip()
    if not val:
        return 0
    try:
        idx = int(val)
        if 0 <= idx < len(shown):
            return idx
    except ValueError:
        pass
    print("  Entrada inválida, usando a mais recente.")
    return 0


def _process_modpack_target(target, loader: str, game_version: str, dest: Path) -> None:
    files = target.version["files"]
    primary = next((f for f in files if f.get("primary")), files[0])
    tmp_entry = {
        "path": primary["filename"],
        "url": primary["url"],
        "hashes": primary.get("hashes", {}),
    }
    print("Baixando o .mrpack da versão escolhida...")
    downloader.download_all([tmp_entry], dest)
    tmp_mrpack = dest / primary["filename"]

    # esse .mrpack foi baixado só como passo intermediário: remove depois de extrair
    result = packer.unpack_local_mrpack(tmp_mrpack, dest, delete_mrpack_after=True)
    _report(result["download_result"])


def _process_loose_mod_target(target, loader: str, game_version: str, dest: Path,
                            include_optional: bool) -> None:
    print("Resolvendo dependências...")
    resolved = dependency_resolver.resolve_dependencies(
        target.version, loader, game_version, include_optional=include_optional
    )
    print(f"Total a baixar (mod + dependências): {len(resolved)}")
    result = packer.pack_loose_mods(resolved, dest)
    _report(result["download_result"])


def run() -> None:
    """Modo interativo: pergunta tudo por input()."""
    print("=== Modrinth Toolkit ===\n")

    modo = ask(
        "A entrada é: (1) link/slug/id do Modrinth  ou  (2) arquivo .mrpack local? [1/2]: ",
        ["1", "2"],
    )

    dest = Path(ask("Pasta de destino onde montar a instância: "))
    dest.mkdir(parents=True, exist_ok=True)

    if modo == "2":
        caminho = ask("Caminho do arquivo .mrpack: ")
        target = resolver.resolve_from_local_file(caminho)
        print(f"\nModpack local detectado: {target.project_name}")
        # arquivo local é do próprio usuário, não deve ser removido depois de extrair
        result = packer.unpack_local_mrpack(target.local_mrpack_path, dest, delete_mrpack_after=False)
        _report(result["download_result"])
        print(f"\nPronto! Instância montada em: {dest}")
        return

    link_ou_id = ask("Cole o link, slug ou id do Modrinth: ")
    loader = ask(f"Loader ({'/'.join(LOADERS)}): ", LOADERS)
    game_version = ask("Versão do Minecraft (ex: 1.21.1): ")

    project, versions = resolver.list_compatible_versions(link_ou_id, loader, game_version)
    version_index = _choose_version_interactively(project, versions)
    target = resolver.resolve_from_link_or_id(link_ou_id, loader, game_version, version_index)
    print(f"\nEscolhido: {target.project_name} v{target.version.get('version_number', '?')} "
        f"(tipo: {target.project_type})")

    if target.project_type == "modpack":
        _process_modpack_target(target, loader, game_version, dest)
    else:
        include_optional = ask_yes_no(
            "Incluir também dependências opcionais (addons/compat recomendados)?"
        )
        _process_loose_mod_target(target, loader, game_version, dest, include_optional)

    print(f"\nPronto! Instância montada em: {dest}")


def run_noninteractive(args) -> None:
    """
    Modo não-interativo, pra automação/scripts/futura GUI.
    `args` é o resultado de argparse com os campos: mrpack, link, loader,
    mc_version, dest, version_index, include_optional.
    """
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    if args.mrpack:
        target = resolver.resolve_from_local_file(args.mrpack)
        log.info(f"Modpack local detectado: {target.project_name}")
        result = packer.unpack_local_mrpack(target.local_mrpack_path, dest, delete_mrpack_after=False)
        _report(result["download_result"])
        log.info(f"Pronto! Instância montada em: {dest}")
        return

    if not (args.link and args.loader and args.mc_version):
        raise SystemExit(
            "Modo não-interativo com link precisa de --link, --loader e --mc-version."
        )

    target = resolver.resolve_from_link_or_id(
        args.link, args.loader, args.mc_version, version_index=args.version_index
    )
    log.info(f"Escolhido: {target.project_name} v{target.version.get('version_number', '?')} "
            f"(tipo: {target.project_type})")

    if target.project_type == "modpack":
        _process_modpack_target(target, args.loader, args.mc_version, dest)
    else:
        _process_loose_mod_target(target, args.loader, args.mc_version, dest, args.include_optional)

    log.info(f"Pronto! Instância montada em: {dest}")


if __name__ == "__main__":
    run()
