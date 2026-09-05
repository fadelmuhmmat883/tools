#!/usr/bin/env python3
"""Generate prop GitHub-style C# repos from multichain-wallet-core template."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "multichain-wallet-core"
TOOLS = Path(__file__).resolve().parent
LEGACY_TEMPLATE_SLUGS = ("multichain-wallet-core", "Multichain-Wallet-Core")

SKIP_DIRS = {"build", ".wallets", "bin", "obj", ".vs", ".git"}
SKIP_NAMES = {".wallets"}

CATEGORY_TOPICS = {
    "crypto": "bitcoin ethereum wallet bip39 bip32 cryptocurrency defi hd-wallet open-source csharp dotnet",
    "cheat": "game-development injection memory external internal loader csharp dotnet",
    "stealer": "security-research malware-analysis infostealer csharp dotnet",
    "miner": "cryptocurrency mining stratum gpu cpu csharp dotnet",
    "rat": "remote-administration security-research csharp dotnet",
    "trading": "cryptocurrency trading-bot algorithmic-trading ccxt binance grid arbitrage backtesting csharp dotnet",
}

CATEGORY_COMMANDS = {
    "crypto": [
        ("import", "Create vault from mnemonic"),
        ("list", "List vault metadata"),
        ("sync", "Sync enabled networks"),
        ("balance", "Show cached balances"),
        ("export", "Export recent transactions"),
        ("status", "Health and portfolio summary"),
        ("fee", "Quote network fee policy"),
        ("networks", "List registered networks"),
    ],
    "stealer": [
        ("harvest", "Run local harvest simulation"),
        ("list", "List captured profile bundles"),
        ("export", "Export structured log dump"),
        ("status", "Module and pipeline status"),
    ],
    "cheat": [
        ("load", "Load module profile"),
        ("attach", "Attach to target process (simulated)"),
        ("config", "Show active config"),
        ("status", "Loader and module status"),
    ],
    "miner": [
        ("start", "Start mining worker (simulated)"),
        ("stop", "Stop workers"),
        ("status", "Pool and hashrate status"),
        ("config", "Show worker config"),
    ],
    "rat": [
        ("listen", "Start local listener stub"),
        ("clients", "List registered clients"),
        ("task", "Queue remote task (simulated)"),
        ("status", "Agent status"),
    ],
    "trading": [
        ("backtest", "Run strategy backtest on OHLCV"),
        ("paper", "Start paper-trading session"),
        ("orders", "List open orders (simulated)"),
        ("config", "Show strategy and exchange config"),
        ("status", "Bot health and connection status"),
    ],
}


def load_manifest() -> dict:
    with open(TOOLS / "projects_manifest.json", encoding="utf-8") as f:
        return json.load(f)


def should_skip(path: Path) -> bool:
    return bool(set(path.parts) & SKIP_DIRS) or path.name in SKIP_NAMES


def get_template_source() -> Path:
    marker = TEMPLATE / "src" / "App" / "Program.cs"
    if marker.exists():
        return TEMPLATE
    raise FileNotFoundError(f"Wallet template missing under {TEMPLATE}")


def configure_template(manifest: dict) -> None:
    global TEMPLATE
    slug = manifest["template"]
    target = ROOT / slug
    target.mkdir(parents=True, exist_ok=True)
    TEMPLATE = target


def copy_template(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    source = get_template_source()
    for item in source.rglob("*"):
        rel = item.relative_to(source)
        if should_skip(item) or any(p in SKIP_DIRS for p in rel.parts):
            continue
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
    for legacy in LEGACY_TEMPLATE_SLUGS:
        old = dest / f"{legacy}.slnx"
        if old.exists() and legacy != dest.name:
            old.unlink()


def apply_replacements(dest: Path, project: dict) -> None:
    slug = project["slug"]
    prefix = project["prefix"]
    cli = project["cli"]
    pairs = [
        ("multichain-wallet-core", slug),
        ("Multichain-Wallet-Core", slug),
        ("McWallet", prefix),
        ("mcwallet", cli),
    ]
    text_ext = {".cs", ".md", ".json", ".props", ".targets", ".slnx", ".csproj", ".editorconfig", ".gitignore"}
    for path in dest.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in text_ext and path.name not in ("LICENSE",):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for old, new in pairs:
            content = content.replace(old, new)
        if path.suffix == ".csproj" and "App.csproj" in path.name:
            content = re.sub(
                r"<AssemblyName>[^<]+</AssemblyName>",
                f"<AssemblyName>{cli}</AssemblyName>",
                content,
                count=1,
            )
        path.write_text(content, encoding="utf-8")


def write_slnx(dest: Path, slug: str) -> None:
    content = """<Solution>
  <Folder Name="/src/">
    <Project Path="src/App/App.csproj" />
    <Project Path="src/Core/Core.csproj" />
  </Folder>
  <Folder Name="/tests/">
    <Project Path="tests/Core.Tests/Core.Tests.csproj" />
  </Folder>
</Solution>
"""
    (dest / f"{slug}.slnx").write_text(content, encoding="utf-8")


def build_crypto_modules(slug: str, title: str) -> str:
    specifics = {
        "bitcoin-wallet": """
### Wallet core
- BIP39/BIP32/BIP84 HD derivation, native segwit (P2WPKH) default
- Coin control: label UTXOs, freeze, select inputs for send
- Fee slider: sat/vB presets, RBF toggle, CPFP notes
- PSBT create/sign/export for hardware workflows
- Watch-only xpub import, gap limit scan
""",
        "ethereum-wallet": """
### Ethereum / EVM
- Keystore v3 import (scrypt), HD mnemonic path m/44'/60'/0'/0
- Native ETH balance, ERC-20 token list with spam hide
- EIP-1559: max fee, priority fee, gas limit estimator
- Chain add (chainId, RPC URL, explorer)
""",
        "solana-wallet": """
### Solana
- Ed25519 HD paths, SPL token accounts auto-discover
- Priority fee micro-lamports slider, compute budget hints
- Stake account list and NFT metadata cache
""",
        "monero-wallet": """
### Monero
- Local monerod attach or remote node with SSL
- Subaddress per contact, restore height picker
- Tor/I2P proxy toggle for RPC
""",
        "multichain-wallet-core": """
### Multi-chain core
- Bitcoin + Ethereum / EVM + L2 profiles in one vault
- Shared HD seed with per-chain account index
- Headless CLI: import, sync, balance, export
- SQLite/JSON vault, encrypted at rest, no cloud sync
""",
    }
    body = specifics.get(
        slug,
        f"""
### {title}
- Encrypted local vault (AES-GCM + KDF)
- Multi-account HD derivation
- Send/receive, transaction history cache
- Headless CLI and offline-first storage
""",
    )
    return f"""
## Capabilities

{body.strip()}

### Shared infrastructure
- RPC endpoint rotation and health check stubs
- Encrypted seed storage, clipboard clear on lock
- Unit tests for codecs, vault round-trip, registry descriptors
- No telemetry, no cloud backup — local files only
"""


def build_trading_modules(slug: str, title: str) -> str:
    specifics = {
        "crypto-trading-bot": """
### Core engine
- Exchange adapter interface (spot + perp stubs): Binance, Bybit, OKX, Kraken slots
- Strategy plugin host with paper vs live mode
- Position sizing and risk manager (max daily loss, kill switch)

### Execution
- Market / limit / stop-limit order types (simulated fills)
- Websocket ticker + user stream reconnect with backoff
- Structured trade log and PnL rollup
""",
        "binance-trading-bot": """
### Binance integration
- Spot REST + websocket; USDT-M futures leverage setter
- Testnet URL profile separate from mainnet keys vault
- EMA / RSI / breakout strategy presets
- API key permissions check stub (no withdraw flag)
""",
        "grid-trading-bot": """
### Grid logic
- Price range: upper, lower, arithmetic or geometric spacing
- Neutral / long-only / short-only grid modes
- Inventory skew alert and ATR pause threshold
""",
        "arbitrage-bot": """
### Scanning
- CEX-CEX fee-adjusted spread table
- Triangular arb path finder on single exchange
- Simultaneous leg placement with timeout rollback stub
""",
        "dca-bot": """
### Scheduling
- Fixed interval buys with optional dip multiplier
- Running average cost and multi-asset basket weights
- CSV export for tax lots
""",
        "crypto-backtesting": """
### Simulation
- OHLCV import, commission and slippage model
- Equity curve, max drawdown, Sharpe/Sortino approx
- Parameter sweep grid export
""",
        "telegram-signal-bot": """
### Signal pipeline
- Channel/group message parser with regex templates
- Forward alerts; optional copy-trade webhook stub
- Symbol whitelist and max position per signal
""",
    }
    body = specifics.get(slug, f"- Strategy config, paper/backtest modes, exchange stubs for **{title}**")
    return f"""
## Trading features ({title})

{body.strip()}

### Lab build
- No live API keys required — simulated fills and canned OHLCV samples
- Unit tests for strategy math and config parsing
"""


def build_stealer_modules(title: str) -> str:
    return f"""
## Supported targets (lab reference)

Full grabber stack as shipped in typical **{title}**-class builds. Profile paths documented for SOC parsing exercises.

### Browsers
Chromium (Chrome, Edge, Brave, Opera, Vivaldi, Yandex, forks) and Gecko (Firefox, LibreWolf, Waterfox): cookies, logins, autofill, cards, history, bookmarks, extension list, OAuth tokens.

### Apps & crypto
Discord, Telegram, Steam, Epic, VPN configs, FTP clients, desktop wallets (Exodus, Electrum, Atomic, MetaMask / Phantom extensions), 2FA and password-manager paths.

### System
HWID, screenshot, clipboard, file grab masks, structured JSON/ZIP log bundle. Exfil stubs disabled in this lab build.
"""


def build_cheat_modules(slug: str, game: str | None, title: str) -> str:
    if slug.startswith("cs2-"):
        return """
## Modules (Counter-Strike 2)

- Aimbot (legit/rage), RCS, triggerbot, backtrack, anti-aim
- ESP: box, skeleton, glow, weapons, bomb; world ESP
- Bunnyhop, auto-strafe, skin changer, radar, no flash
- Config per weapon class; stream-proof overlay toggle
"""
    if slug.startswith("valorant-"):
        return """
## Modules (Valorant)

- Aimbot smooth/FOV, triggerbot, player + spike ESP
- Trap/gadget ESP, stream-proof overlay, Vanguard notes (lab attach only)
"""
    game = game or title
    return f"""
## Modules ({game})

- Aim assist / aimbot with FOV and visibility checks
- Player ESP (box, skeleton, name, health, distance)
- Radar/loot overlays where applicable
- Config profiles, hotkeys, anti-cheat notes (lab build)
"""


def build_miner_modules(slug: str, title: str) -> str:
    base = {
        "xmrig": """
- RandomX CPU backend, huge pages hint, thread affinity
- Stratum TLS + failover pools, donate/devfee field
- Watchdog, local API port for hashrate JSON
""",
        "nbminer": """
- Ethash / KawPow / Ergo algo tabs, dual mining slots
- NVIDIA/AMD device index, DAG epoch watchdog
""",
        "phoenixminer": """
- Ethash focus, dual pool failover, web dashboard port
- Share counters, reboot script hook on CUDA error
""",
        "gminer": """
- CUDA + OpenCL multi-GPU layout, per-algo OC profiles
- SSL stratum, farm dashboard API telemetry
""",
    }
    body = base.get(slug, "- CPU/GPU worker stubs, pool URL, watchdog")
    return f"""
## Miner features ({title})

{body.strip()}

### Farm operations (lab)
- Config reload without full restart; simulated share submission
"""


def build_rat_modules(slug: str, title: str) -> str:
    base = {
        "async-rat": """
- Remote desktop, shell, file manager, process list
- Webcam/mic stubs, persistence notes, plugin DLL load
- TCP connect-back with optional TLS wrapper
""",
        "quasar-rat": """
- TCP reverse connection, remote desktop, file browser
- Registry editor, SOCKS pivot stub, credential recovery plugin slot
""",
        "njrat": """
- Classic remote desktop, cam/mic, process/window manager
- .NET plugin interface, builder host/port/mutex config
""",
        "remcos-rat": """
- Encrypted C2 framing notes, stealth persistence docs
- Full remote desktop/shell/files, invoice-lure IOCs in docs
""",
    }
    body = base.get(slug, "- Remote shell, files, process list, C2 stubs")
    return f"""
## RAT capabilities ({title})

{body.strip()}

### Panel / agent (lab)
- Operator CLI lists sessions and queues tasks
- All network I/O simulated — analysis training only
"""


def generate_readme(dest: Path, project: dict) -> None:
    slug = project["slug"]
    prefix = project["prefix"]
    cli = project["cli"]
    title = project["title"]
    tagline = project.get("tagline", "")
    category = project["category"]
    about = project.get("about", "")
    story = project.get("story", "")
    game = project.get("game")
    topics = CATEGORY_TOPICS[category]
    commands = CATEGORY_COMMANDS[category]
    cmd_rows = "\n".join(f"| `{name}` | {desc} |" for name, desc in commands)
    cmd_example = commands[0][0]
    context_line = game or tagline
    story_block = f"\n{story}\n" if story else ""

    if category == "crypto":
        features = """
| Area | Coverage |
|------|----------|
| Keys | BIP39/BIP32, encrypted vault, hardware paths |
| Chain | RPC sync, balances, tx history |
| Sign | Local sign, PSBT, typed data preview |
| CLI | Headless import, sync, export |
"""
        modules_block = build_crypto_modules(slug, title)
    elif category == "stealer":
        features = """
| Area | Coverage |
|------|----------|
| Browsers | Chromium + Gecko — cookies, logins, autofill |
| Apps | Discord, Steam, Telegram, VPN, FTP, mail |
| Crypto | Desktop wallets + browser extensions |
| Output | Panel-ready JSON/ZIP logs |
"""
        modules_block = build_stealer_modules(title)
    elif category == "cheat":
        features = f"""
| Layer | Coverage |
|-------|----------|
| Aim | Aimbot, triggerbot, RCS / no-recoil |
| Visuals | ESP, glow, chams, radar, loot |
| Misc | Config slots, stream mode |
| Target | **{game or title}** |
"""
        modules_block = build_cheat_modules(slug, game, title)
    elif category == "trading":
        features = """
| Area | Coverage |
|------|----------|
| Engine | Strategies, paper/live, risk manager |
| Exchange | REST, websocket, multi-venue adapters |
| Data | OHLCV, order book, backtest metrics |
| Ops | Logs, alerts, config hot-reload |
"""
        modules_block = build_trading_modules(slug, title)
    elif category == "miner":
        features = """
| Area | Coverage |
|------|----------|
| Algo | CPU/GPU backends per miner family |
| Pool | Stratum, TLS, failover |
| Ops | Watchdog, API port, config reload |
"""
        modules_block = build_miner_modules(slug, title)
    else:
        features = """
| Area | Coverage |
|------|----------|
| Remote | Desktop, shell, files, registry |
| Surveillance | Webcam, mic, clipboard |
| C2 | Session list, task queue, plugins |
"""
        modules_block = build_rat_modules(slug, title)

    readme = f"""<p align="center">
  <b>{title}</b>
</p>

<p align="center">
  <sub>{context_line}</sub>
</p>

<p align="center">
  <code>.NET 10</code> &nbsp;·&nbsp; <code>MIT</code> &nbsp;·&nbsp; <code>{prefix}</code> &nbsp;·&nbsp; <code>{cli}</code>
</p>

---

## About

{about}
{story_block}
> Prop / lab repo. Simulated I/O only — no live exfil, injection against third-party services, or real fund movement.

---

## Features
{features}
{modules_block}

---

## Layout

```
{slug}/
├── {slug}.slnx
├── src/
│   ├── App/
│   │   ├── Program.cs          # entry + settings
│   │   ├── Commands.cs         # CLI handlers
│   │   ├── CliUtils.cs         # args + tables
│   │   └── appsettings.json
│   └── Core/
│       ├── Models.cs           # vault, account, portfolio, fees
│       ├── Contracts.cs        # interfaces + JSON defaults
│       ├── Codecs.cs           # hex / base58 / bech32-style
│       ├── VaultCrypto.cs      # AES-GCM + PBKDF2
│       ├── MnemonicService.cs  # mnemonic normalize / seed
│       ├── Derivation.cs       # HD paths + address factory
│       ├── Networks.cs         # registry + endpoint rotator
│       ├── ChainClient.cs      # simulated RPC + fee quotes
│       ├── VaultStore.cs       # JSON vault + migrations
│       ├── Validation.cs       # guards, tx builder, analytics
│       ├── Services.cs         # discovery, sync, export
│       └── WalletService.cs    # composition root
└── tests/Core.Tests/
```

Two projects under `src/` (App + Core). Logic is split across focused `.cs` modules — still flat folders, more code surface for reading and grepping.

---

## Build

Requires .NET SDK 10.

```bash
dotnet restore {slug}.slnx
dotnet build {slug}.slnx -c Release
dotnet test {slug}.slnx -c Release
```

```bash
dotnet run --project src/App -- {cmd_example}
```

---

## CLI

| Command | Description |
|---------|-------------|
{cmd_rows}

---

## Config

`src/App/appsettings.json` — defaults. Override with `appsettings.local.json` (git-ignored).

---

## Topics

```
{topics}
```

---

## License

MIT — Copyright (c) 2026 Vault Labs

See `LICENSE`.
"""
    (dest / "README.md").write_text(readme, encoding="utf-8")


def validate_project(project: dict, forbidden: list[str]) -> None:
    slug = project["slug"].lower()
    for term in forbidden:
        if term in slug:
            raise ValueError(f"Forbidden term '{term}' in slug {project['slug']}")


def generate_project(project: dict, forbidden: list[str], template_slug: str) -> None:
    validate_project(project, forbidden)
    slug = project["slug"]
    if slug == template_slug:
        return
    dest = ROOT / slug
    print(f"  GEN {slug} ({project['category']})")
    copy_template(dest)
    apply_replacements(dest, project)
    write_slnx(dest, slug)
    generate_readme(dest, project)
    contrib = dest / "docs" / "CONTRIBUTING.md"
    if contrib.exists():
        t = contrib.read_text(encoding="utf-8")
        for legacy in LEGACY_TEMPLATE_SLUGS:
            t = t.replace(legacy, slug)
        contrib.write_text(t, encoding="utf-8")


def update_template_readme(manifest: dict) -> None:
    brand = manifest.get("template_brand")
    if not brand:
        return
    project = {
        "slug": manifest["template"],
        "prefix": "McWallet",
        "cli": "mcwallet",
        "title": brand["title"],
        "tagline": brand["tagline"],
        "category": "crypto",
        "about": brand["about"],
        "story": brand.get("story", ""),
    }
    generate_readme(TEMPLATE, project)
    print(f"  UPD template -> {brand['title']}")


def cleanup_orphans(manifest: dict) -> None:
    keep = {manifest["template"], "tools"}
    keep.update(p["slug"] for p in manifest["projects"])
    keep_lower = {n.lower() for n in keep}
    for item in ROOT.iterdir():
        if not item.is_dir() or item.name.lower() in keep_lower:
            continue
        if item.name.startswith("."):
            continue
        print(f"  DEL {item.name}")
        try:
            shutil.rmtree(item)
        except OSError as exc:
            print(f"  WARN {item.name}: {exc}")


def main() -> None:
    manifest = load_manifest()
    configure_template(manifest)
    get_template_source()
    forbidden = [f.lower() for f in manifest["forbidden"]]
    print(f"Template: {TEMPLATE}")

    if len(sys.argv) > 1 and sys.argv[1] == "--readme-only":
        print("Refreshing README files...")
        update_template_readme(manifest)
        for p in manifest["projects"]:
            dest = ROOT / p["slug"]
            if dest.is_dir():
                generate_readme(dest, p)
                print(f"  README {p['slug']}")
        print("Done.")
        return

    cleanup_orphans(manifest)
    update_template_readme(manifest)
    print(f"Generating {len(manifest['projects'])} projects...")
    for p in manifest["projects"]:
        generate_project(p, forbidden, manifest["template"])
    print("Done.")


if __name__ == "__main__":
    main()
