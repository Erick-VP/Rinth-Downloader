# Rinth Downloader
Ferramenta pra baixar modpacks/mods do Modrinth via **link, slug ou arquivo
`.mrpack` local**, escolhendo **loader** (fabric/forge/neoforge/quilt) e
**versão do Minecraft**, e montar uma pasta de instância pronta pra jogar em
qualquer launcher (TLauncher, MultiMC, instância manual, etc).

## Idiomas:
- 🇺🇸 [English](README.md)
- 🇧🇷 Português (atual)

## Instalação

```bash
pip install -r requirements.txt
```
ou

```bash
python -m pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

A CLI vai perguntar:
1. Se a entrada é um link/slug/id do Modrinth ou um arquivo `.mrpack` local
2. A pasta de destino onde montar a instância
3. (se for link) o loader e a versão do Minecraft desejados

No final, `dest/` vai ter `mods/`, `config/` e tudo mais que o modpack ou
mod precisa, já baixado e verificado por hash.

## Estrutura

```
modrinth_toolkit/
├── modrinth_client.py      # wrapper fino da API pública do Modrinth (v2)
├── resolver.py             # entrada (link/slug/arquivo) -> alvo concreto
├── dependency_resolver.py  # resolve dependências obrigatórias de mods avulsos
├── downloader.py           # download paralelo, hash, retry, cache local
├── packer.py               # monta a pasta final (overrides + mods baixados)
└── cli.py                  # interface interativa que amarra tudo
main.py                     # ponto de entrada
```

## Fluxos suportados

- **Modpack por link/slug** → resolve a versão certa pra loader+MC, baixa o
  `.mrpack` dela, extrai `overrides/` e baixa todos os arquivos do índice.
- **Modpack por arquivo `.mrpack` local** → mesma coisa, sem precisar
  consultar a API pra achar a versão (já está no arquivo).
- **Mod avulso por link/slug** → resolve a versão certa, resolve
  recursivamente as dependências `required`, baixa tudo em `mods/`.

## Cache

Cada arquivo baixado é guardado em `~/.modrinth_toolkit_cache/`, indexado
pelo hash (sha1 ou sha512). Rodar de novo pra um modpack parecido reaproveita
o que já foi baixado antes.

