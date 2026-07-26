"""
CLI interativa: pergunta a entrada (link/arquivo), loader e versão do MC,
e monta a instância final numa pasta de saída escolhida pelo usuário.
"""
from pathlib import Path

from . import dependency_resolver, downloader, packer, resolver

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


def _report(result: dict) -> None:
    print(
        f"\nOK: {len(result['ok'])} | "
        f"Cache: {len(result['cached'])} | "
        f"Falharam: {len(result['failed'])}"
    )
    for f in result["failed"]:
        print(f"  - {f['path']}: {f['error']}")


def run() -> None:
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
        result = packer.unpack_local_mrpack(target.local_mrpack_path, dest)
        _report(result["download_result"])
        print(f"\nPronto! Instância montada em: {dest}")
        return

    link_ou_id = ask("Cole o link, slug ou id do Modrinth: ")
    loader = ask(f"Loader ({'/'.join(LOADERS)}): ", LOADERS)
    game_version = ask("Versão do Minecraft (ex: 1.21.1): ")

    target = resolver.resolve_from_link_or_id(link_ou_id, loader, game_version)
    print(f"\nEncontrado: {target.project_name}  (tipo: {target.project_type})")

    if target.project_type == "modpack":
        # baixa o .mrpack dessa versão específica e processa como pacote local
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

        result = packer.unpack_local_mrpack(tmp_mrpack, dest)
        _report(result["download_result"])
    else:
        # mod avulso: resolve dependências obrigatórias e baixa tudo junto
        print("Resolvendo dependências obrigatórias...")
        resolved = dependency_resolver.resolve_dependencies(
            target.version, loader, game_version
        )
        print(f"Total a baixar (mod + dependências): {len(resolved)}")
        result = packer.pack_loose_mods(resolved, dest)
        _report(result["download_result"])

    print(f"\nPronto! Instância montada em: {dest}")


if __name__ == "__main__":
    run()
