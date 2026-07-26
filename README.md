# Rinth Downloader

A tool for downloading Modrinth modpacks and mods using a **link, slug, or local
`.mrpack` file**, allowing you to choose the **loader** (Fabric, Forge,
NeoForge, or Quilt) and **Minecraft version**, then build a ready-to-play
instance folder compatible with any launcher (TLauncher, MultiMC, manual
instance, etc.).

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

```
modrinth_toolkit/
├── modrinth_client.py      # Thin wrapper around the Modrinth public API (v2)
├── resolver.py             # Resolves link/slug/file into a concrete target
├── dependency_resolver.py  # Resolves required dependencies for standalone mods
├── downloader.py           # Parallel downloads, hash verification, retries, local cache
├── packer.py               # Builds the final instance (overrides + downloaded mods)
└── cli.py                  # Interactive CLI that ties everything together
main.py                     # Entry point
```

## Supported Workflows

- **Modpack from link/slug** → Finds the correct version for the selected
  loader and Minecraft version, downloads its `.mrpack`, extracts
  `overrides/`, and downloads every file listed in the manifest.
- **Modpack from a local `.mrpack` file** → Same process, without querying
  the API since the version information is already contained in the file.
- **Standalone mod from link/slug** → Finds the correct version, recursively
  resolves all `required` dependencies, and downloads everything into
  `mods/`.

## Cache

Every downloaded file is stored in
`~/.modrinth_toolkit_cache/`, indexed by its hash (SHA-1 or SHA-512). Running
the tool again for a similar modpack will automatically reuse files that have
already been downloaded.