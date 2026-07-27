# Rinth Downloader
Ferramenta pra baixar modpacks/mods do Modrinth via **link, slug ou arquivo
`.mrpack` local**, escolhendo **loader** (fabric/forge/neoforge/quilt) e
**versão do Minecraft**, e montar uma pasta de instância pronta pra jogar em
qualquer launcher (TLauncher, MultiMC, instância manual, etc).

## Idiomas:
- 🇺🇸 [English](README.md)
- 🇧🇷 Português (atual)

## Dependências

- Python 3.10+
- Requests (incluído em `requirements.txt`)


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
├── modrinth_client.py      # wrapper da API do Modrinth: rate limit, retry/backoff, checa formatVersion
├── rate_limiter.py         # limitador reutilizável (também pronto pra CurseForge no futuro)
├── logging_setup.py        # log em tela (INFO) + arquivo (DEBUG) em ~/.modrinth_toolkit_logs
├── resolver.py             # entrada (link/slug/arquivo) -> alvo concreto, com listagem de versões
├── dependency_resolver.py  # resolve dependências (required, e opcional se pedido)
├── downloader.py           # download paralelo, hash, retry, cache local
├── packer.py               # monta a pasta final (overrides + mods baixados, na pasta certa por tipo)
└── cli.py                  # interativa (input()) e não-interativa (argparse), mesma lógica por baixo
main.py                     # ponto de entrada; sem args = interativo, com --link/--mrpack = não-interativo
```

## Modo não-interativo (automação)

```bash
# modpack por link
python main.py --link create-plus --loader neoforge --mc-version 1.21.1 --dest ./instancia

# mod avulso, incluindo dependências opcionais
python main.py --link sodium --loader fabric --mc-version 1.21.1 --dest ./instancia --include-optional

# a partir de um .mrpack local
python main.py --mrpack ./Create__6_0_0_Alpha_f.mrpack --dest ./instancia
```

## Logs

Tudo que acontece fica salvo em `~/.modrinth_toolkit_logs/modrinth_toolkit.log`
(nível DEBUG, com detalhes de erro que não aparecem na tela). Útil pra
debugar se algo falhar no meio de um download grande.

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