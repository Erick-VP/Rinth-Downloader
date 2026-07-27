#!/usr/bin/env python3
"""
Ponto de entrada.

Modo interativo (pergunta tudo):
    python main.py

Modo não-interativo (automação/scripts), modpack por link:
    python main.py --link create-plus --loader neoforge --mc-version 1.21.1 --dest ./instancia

Modo não-interativo, mod avulso incluindo dependências opcionais:
    python main.py --link sodium --loader fabric --mc-version 1.21.1 --dest ./instancia --include-optional

Modo não-interativo, a partir de um .mrpack local:
    python main.py --mrpack ./Create__6_0_0_Alpha_f.mrpack --dest ./instancia
"""
import argparse

from modrinth_toolkit import cli


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Modrinth Toolkit — baixa mods/modpacks do Modrinth.")
    p.add_argument("--link", help="Link, slug ou id do Modrinth (mod ou modpack).")
    p.add_argument("--mrpack", help="Caminho de um arquivo .mrpack local.")
    p.add_argument("--loader", choices=["fabric", "forge", "neoforge", "quilt"],
                    help="Loader desejado (obrigatório se usar --link).")
    p.add_argument("--mc-version", dest="mc_version",
                    help="Versão do Minecraft, ex: 1.21.1 (obrigatório se usar --link).")
    p.add_argument("--dest", default="./instancia",
                    help="Pasta de destino onde montar a instância (padrão: ./instancia).")
    p.add_argument("--version-index", dest="version_index", type=int, default=0,
                    help="Índice da versão compatível a usar, 0 = mais recente (padrão: 0).")
    p.add_argument("--include-optional", dest="include_optional", action="store_true",
                    help="Também baixa dependências opcionais (só se aplica a mod avulso).")
    return p


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.link or args.mrpack:
        cli.run_noninteractive(args)
    else:
        cli.run()
