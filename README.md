# Rinth Downloader

A tool for downloading Modrinth modpacks and mods using a **link, slug, or local
`.mrpack` file**, allowing you to choose the **loader** (Fabric, Forge,
NeoForge, or Quilt) and **Minecraft version**, then build a ready-to-play
instance compatible with any launcher (TLauncher, MultiMC, manual instance,
etc.).

## Languages

- 🇺🇸 English (current)
- 🇧🇷 [Português](README.pt-BR.md)

## Installation

```bash
pip install -r requirements.txt
```

or

```bash
python -m pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The CLI will ask for:

1. Whether the input is a Modrinth link/slug/ID or a local `.mrpack` file.
2. The destination folder where the instance should be created.
3. (For links) The desired loader and Minecraft version.

When finished, the `dest/` directory will contain `mods/`, `config/`, and
everything else required by the modpack or mod, already downloaded and
verified using hashes.

## Project Structure

```text
modrinth_toolkit/
├── modrinth_client.py      # Modrinth API wrapper: rate limiting, retry/backoff, validates formatVersion
├── rate_limiter.py         # Reusable rate limiter (also ready for CurseForge support in the future)
├── logging_setup.py        # Console logging (INFO) + file logging (DEBUG) at ~/.modrinth_toolkit_logs
├── resolver.py             # Resolves link/slug/file into a concrete target, with version selection
├── dependency_resolver.py  # Resolves dependencies (required, and optional if requested)
├── downloader.py           # Parallel downloads, hash verification, retries, local cache
├── packer.py               # Builds the final instance (overrides + downloaded files, placed in the correct folders)
└── cli.py                  # Interactive (input()) and non-interactive (argparse) interfaces using the same core logic
main.py                     # Entry point; no arguments = interactive mode, --link/--mrpack = non-interactive mode
```

## Non-Interactive Mode (Automation)

```bash
# Modpack from a link
python main.py --link create-plus --loader neoforge --mc-version 1.21.1 --dest ./instance

# Standalone mod, including optional dependencies
python main.py --link sodium --loader fabric --mc-version 1.21.1 --dest ./instance --include-optional

# From a local .mrpack file
python main.py --mrpack ./Create__6_0_0_Alpha_f.mrpack --dest ./instance
```

## Logs

Everything the application does is logged to
`~/.modrinth_toolkit_logs/modrinth_toolkit.log` (DEBUG level, including
error details that are not shown in the console). This is useful for
debugging if something fails during a large download.

## Supported Workflows

- **Modpack from a link/slug** → Finds the correct version for the selected
  loader and Minecraft version, downloads its `.mrpack`, extracts
  `overrides/`, and downloads every file listed in the manifest.
- **Modpack from a local `.mrpack` file** → Same process, without querying
  the API since the version information is already contained in the file.
- **Standalone mod from a link/slug** → Finds the correct version,
  recursively resolves all `required` dependencies, and downloads everything
  into `mods/`.

## Cache

Every downloaded file is stored in
`~/.modrinth_toolkit_cache/`, indexed by its hash (SHA-1 or SHA-512). Running
the tool again for a similar modpack automatically reuses files that have
already been downloaded.