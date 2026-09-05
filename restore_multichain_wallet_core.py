#!/usr/bin/env python3
"""Restore multichain-wallet-core McWallet template from agent transcript."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "multichain-wallet-core"
TRANSCRIPT = Path(
    r"C:\Users\chipk\.cursor\projects\c-Project-A-Projects\agent-transcripts"
    r"\b8ef7822-320f-40e4-a5ef-59bbac11782e\b8ef7822-320f-40e4-a5ef-59bbac11782e.jsonl"
)

# Old MultiChainWallet path -> new McWallet path (from transcript shell migration)
COPY_MAP: list[tuple[str, str]] = [
    ("src/MultiChainWallet.Cli/Program.cs", "src/App/Program.cs"),
    ("src/MultiChainWallet.Cli/appsettings.json", "src/App/appsettings.json"),
    ("src/MultiChainWallet.Cli/ConsoleOutputFormatter.cs", "src/App/Output/ConsoleOutputFormatter.cs"),
    ("src/MultiChainWallet.Cli/Infrastructure/ServiceBootstrapper.cs", "src/App/Bootstrap/ServiceBootstrapper.cs"),
    ("src/MultiChainWallet.Cli/Infrastructure/CommandRouter.cs", "src/App/Bootstrap/CommandRouter.cs"),
    ("src/MultiChainWallet.Core/Configuration/WalletOptions.cs", "src/Engine/Options/WalletOptions.cs"),
    ("src/MultiChainWallet.Core/WalletManager.cs", "src/Engine/Orchestration/WalletManager.cs"),
    ("src/MultiChainWallet.Core/SyncCoordinator.cs", "src/Engine/Orchestration/SyncCoordinator.cs"),
    ("src/MultiChainWallet.Core/DefaultWalletProvider.cs", "src/Engine/Orchestration/DefaultWalletProvider.cs"),
    ("src/MultiChainWallet.Core/KeyDerivationService.cs", "src/Engine/Orchestration/KeyDerivationService.cs"),
    ("src/MultiChainWallet.Core/BalanceAggregator.cs", "src/Engine/Analytics/BalanceAggregator.cs"),
    ("src/MultiChainWallet.Core/TransactionPipeline.cs", "src/Engine/Analytics/TransactionPipeline.cs"),
    ("src/MultiChainWallet.Core/NetworkRegistry.cs", "src/Engine/Networks/NetworkRegistry.cs"),
    ("src/MultiChainWallet.Core/AddressValidator.cs", "src/Engine/Networks/AddressValidator.cs"),
    ("src/MultiChainWallet.Core/DerivationPathResolver.cs", "src/Engine/Networks/DerivationPathResolver.cs"),
    ("src/MultiChainWallet.Crypto/Bip39MnemonicProcessor.cs", "src/Cryptography/Derivation/Bip39MnemonicProcessor.cs"),
    ("src/MultiChainWallet.Crypto/Bip32KeyDeriver.cs", "src/Cryptography/Derivation/Bip32KeyDeriver.cs"),
    ("src/MultiChainWallet.Crypto/VaultEncryptor.cs", "src/Cryptography/Vault/VaultEncryptor.cs"),
    ("src/MultiChainWallet.Crypto/Pbkdf2Provider.cs", "src/Cryptography/Vault/Pbkdf2Provider.cs"),
    ("src/MultiChainWallet.Crypto/ScryptKdf.cs", "src/Cryptography/Vault/ScryptKdf.cs"),
    ("src/MultiChainWallet.Crypto/Secp256k1Signer.cs", "src/Cryptography/Signing/Secp256k1Signer.cs"),
    ("src/MultiChainWallet.Crypto/Base58Encoder.cs", "src/Cryptography/Codecs/Base58Encoder.cs"),
    ("src/MultiChainWallet.Crypto/Bech32Encoder.cs", "src/Cryptography/Codecs/Bech32Encoder.cs"),
    ("src/MultiChainWallet.Crypto/Sha256Hasher.cs", "src/Cryptography/Codecs/Sha256Hasher.cs"),
    ("src/MultiChainWallet.Crypto/Keccak256Hasher.cs", "src/Cryptography/Codecs/Keccak256Hasher.cs"),
    ("src/MultiChainWallet.Crypto/HmacProvider.cs", "src/Cryptography/Codecs/HmacProvider.cs"),
    ("src/MultiChainWallet.Network/EthereumRpcClient.cs", "src/ChainProviders/Evm/EthereumRpcClient.cs"),
    ("src/MultiChainWallet.Network/PolygonRpcClient.cs", "src/ChainProviders/Evm/PolygonRpcClient.cs"),
    ("src/MultiChainWallet.Network/Clients/BscRpcClient.cs", "src/ChainProviders/Evm/BscRpcClient.cs"),
    ("src/MultiChainWallet.Network/BitcoinRpcClient.cs", "src/ChainProviders/Utxo/BitcoinRpcClient.cs"),
    ("src/MultiChainWallet.Network/HttpTransportLayer.cs", "src/ChainProviders/Transport/HttpTransportLayer.cs"),
    ("src/MultiChainWallet.Network/EndpointRotator.cs", "src/ChainProviders/Transport/EndpointRotator.cs"),
    ("src/MultiChainWallet.Network/RateLimitHandler.cs", "src/ChainProviders/Transport/RateLimitHandler.cs"),
    ("src/MultiChainWallet.Network/JsonRpcModels.cs", "src/ChainProviders/Transport/JsonRpcModels.cs"),
    ("src/MultiChainWallet.Network/RpcClientBase.cs", "src/ChainProviders/Transport/RpcClientBase.cs"),
    ("src/MultiChainWallet.Network/BlockHeaderParser.cs", "src/ChainProviders/Transport/BlockHeaderParser.cs"),
    ("src/MultiChainWallet.Network/Pool/ConnectionPoolManager.cs", "src/ChainProviders/Transport/ConnectionPoolManager.cs"),
    ("src/MultiChainWallet.Storage/SqliteWalletStore.cs", "src/Persistence/Stores/SqliteWalletStore.cs"),
    ("src/MultiChainWallet.Storage/MigrationRunner.cs", "src/Persistence/Stores/MigrationRunner.cs"),
    ("src/MultiChainWallet.Storage/EncryptedVaultRepository.cs", "src/Persistence/Stores/EncryptedVaultRepository.cs"),
    ("src/MultiChainWallet.Storage/TransactionCache.cs", "src/Persistence/Stores/TransactionCache.cs"),
    ("src/MultiChainWallet.Storage/FileLockManager.cs", "src/Persistence/Stores/FileLockManager.cs"),
    ("src/MultiChainWallet.Storage/BackupSnapshotService.cs", "src/Persistence/Stores/BackupSnapshotService.cs"),
    ("src/MultiChainWallet.Storage/SchemaDefinitions.cs", "src/Persistence/Schema/SchemaDefinitions.cs"),
]

GLOB_COPY: list[tuple[str, str]] = [
    ("src/MultiChainWallet.Cli/Commands/*.cs", "src/App/Commands"),
    ("src/MultiChainWallet.Core/Models/*.cs", "src/Engine/Domain/Models"),
    ("src/MultiChainWallet.Core/Interfaces/*.cs", "src/Engine/Domain/Contracts"),
    ("src/MultiChainWallet.Core/Extensions/*.cs", "src/Engine/Domain/Extensions"),
    ("src/MultiChainWallet.Core/Services/*.cs", "src/Engine/Orchestration"),
    ("src/MultiChainWallet.Core/Validation/*.cs", "src/Engine/Validation"),
    ("src/MultiChainWallet.Crypto/Mnemonic/*.cs", "src/Cryptography/Mnemonic"),
    ("src/MultiChainWallet.Crypto/Codecs/*.cs", "src/Cryptography/Codecs"),
    ("src/MultiChainWallet.Network/Resilience/*.cs", "src/ChainProviders/Resilience"),
    ("src/MultiChainWallet.Storage/Repositories/*.cs", "src/Persistence/Repositories"),
    ("src/MultiChainWallet.Storage/Indexing/*.cs", "src/Persistence/Indexing"),
    ("src/MultiChainWallet.Storage/Maintenance/*.cs", "src/Persistence/Maintenance"),
    ("tests/MultiChainWallet.Core.Tests/*.cs", "tests/Engine.Tests"),
    ("tests/MultiChainWallet.Crypto.Tests/*.cs", "tests/Cryptography.Tests"),
]

NAMESPACE_REPLACEMENTS = [
    ("namespace MultiChainWallet.Core.Models;", "namespace McWallet.Engine.Domain.Models;"),
    ("namespace MultiChainWallet.Core.Interfaces;", "namespace McWallet.Engine.Domain.Contracts;"),
    ("namespace MultiChainWallet.Core.Extensions;", "namespace McWallet.Engine.Domain.Extensions;"),
    ("namespace MultiChainWallet.Core.Configuration;", "namespace McWallet.Engine.Options;"),
    ("namespace MultiChainWallet.Core.Validation;", "namespace McWallet.Engine.Validation;"),
    ("namespace MultiChainWallet.Core.Services;", "namespace McWallet.Engine.Orchestration;"),
    ("namespace MultiChainWallet.Core;", "namespace McWallet.Engine.Orchestration;"),
    ("namespace MultiChainWallet.Crypto.Mnemonic;", "namespace McWallet.Cryptography.Mnemonic;"),
    ("namespace MultiChainWallet.Crypto.Codecs;", "namespace McWallet.Cryptography.Codecs;"),
    ("namespace MultiChainWallet.Crypto;", "namespace McWallet.Cryptography.Derivation;"),
    ("namespace MultiChainWallet.Network.Clients;", "namespace McWallet.ChainProviders.Evm;"),
    ("namespace MultiChainWallet.Network.Resilience;", "namespace McWallet.ChainProviders.Resilience;"),
    ("namespace MultiChainWallet.Network.Pool;", "namespace McWallet.ChainProviders.Transport;"),
    ("namespace MultiChainWallet.Network;", "namespace McWallet.ChainProviders.Transport;"),
    ("namespace MultiChainWallet.Storage.Repositories;", "namespace McWallet.Persistence.Repositories;"),
    ("namespace MultiChainWallet.Storage.Indexing;", "namespace McWallet.Persistence.Indexing;"),
    ("namespace MultiChainWallet.Storage.Maintenance;", "namespace McWallet.Persistence.Maintenance;"),
    ("namespace MultiChainWallet.Storage;", "namespace McWallet.Persistence.Stores;"),
    ("namespace MultiChainWallet.Cli.Commands;", "namespace McWallet.App.Commands;"),
    ("namespace MultiChainWallet.Cli.Infrastructure;", "namespace McWallet.App.Bootstrap;"),
    ("namespace MultiChainWallet.Cli;", "namespace McWallet.App;"),
    ("using MultiChainWallet.Core.Models;", "using McWallet.Engine.Domain.Models;"),
    ("using MultiChainWallet.Core.Interfaces;", "using McWallet.Engine.Domain.Contracts;"),
    ("using MultiChainWallet.Core.Extensions;", "using McWallet.Engine.Domain.Extensions;"),
    ("using MultiChainWallet.Core.Configuration;", "using McWallet.Engine.Options;"),
    ("using MultiChainWallet.Core.Validation;", "using McWallet.Engine.Validation;"),
    ("using MultiChainWallet.Core.Services;", "using McWallet.Engine.Orchestration;"),
    ("using MultiChainWallet.Core;", "using McWallet.Engine.Orchestration;"),
    ("using MultiChainWallet.Crypto.Mnemonic;", "using McWallet.Cryptography.Mnemonic;"),
    ("using MultiChainWallet.Crypto.Codecs;", "using McWallet.Cryptography.Codecs;"),
    ("using MultiChainWallet.Crypto;", "using McWallet.Cryptography.Derivation;"),
    ("using MultiChainWallet.Network.Clients;", "using McWallet.ChainProviders.Evm;"),
    ("using MultiChainWallet.Network.Resilience;", "using McWallet.ChainProviders.Resilience;"),
    ("using MultiChainWallet.Network;", "using McWallet.ChainProviders.Transport;"),
    ("using MultiChainWallet.Storage.Repositories;", "using McWallet.Persistence.Repositories;"),
    ("using MultiChainWallet.Storage.Indexing;", "using McWallet.Persistence.Indexing;"),
    ("using MultiChainWallet.Storage.Maintenance;", "using McWallet.Persistence.Maintenance;"),
    ("using MultiChainWallet.Storage;", "using McWallet.Persistence.Stores;"),
    ("using MultiChainWallet.Cli.Commands;", "using McWallet.App.Commands;"),
    ("using MultiChainWallet.Cli.Infrastructure;", "using McWallet.App.Bootstrap;"),
    ("using MultiChainWallet.Cli;", "using McWallet.App;"),
    ("global::MultiChainWallet.Storage.SqliteWalletStore", "global::McWallet.Persistence.Stores.SqliteWalletStore"),
    ("MultiChainWallet.Core.Tests", "McWallet.Engine.Tests"),
    ("MultiChainWallet.Crypto.Tests", "McWallet.Cryptography.Tests"),
]

FOLDER_NAMESPACE_FIXES: dict[str, str] = {
    "src/Engine/Analytics": "McWallet.Engine.Analytics",
    "src/Engine/Networks": "McWallet.Engine.Networks",
    "src/Cryptography/Vault": "McWallet.Cryptography.Vault",
    "src/Cryptography/Signing": "McWallet.Cryptography.Signing",
    "src/ChainProviders/Evm": "McWallet.ChainProviders.Evm",
    "src/ChainProviders/Utxo": "McWallet.ChainProviders.Utxo",
    "src/Persistence/Schema": "McWallet.Persistence.Schema",
    "src/App/Output": "McWallet.App.Output",
}

# McWallet-era files written directly (override migrated copies)
MCWALLET_DIRECT = {
    "src/App",
    "src/App/Bootstrap",
    "src/App/Commands",
    "src/App/Output",
    "src/App/App.csproj",
    "src/Engine/Engine.csproj",
    "src/Cryptography/Cryptography.csproj",
    "src/ChainProviders/ChainProviders.csproj",
    "src/Persistence/Persistence.csproj",
    "tests/Engine.Tests/Engine.Tests.csproj",
    "tests/Cryptography.Tests/Cryptography.Tests.csproj",
    "multichain-wallet-core.slnx",
    "Directory.Build.props",
    "docs/STRUCTURE.md",
}

SKIP_OUTPUT_PREFIXES = (
    "multichain-wallet-core.sln",
    "Directory.Build.targets",
    "nuget.config",
    "src/MultiChainWallet.Abstractions",
)


def should_skip_output(rel: str) -> bool:
    return any(rel.startswith(x) for x in SKIP_OUTPUT_PREFIXES)


def norm_path(p: str) -> str:
    if "multichain-wallet-core" in p.replace("\\", "/").lower():
        parts = p.replace("\\", "/").split("multichain-wallet-core/")
        if len(parts) > 1:
            return parts[-1].lstrip("/")
    return p.replace("\\", "/").lstrip("/")


def parse_transcript() -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    writes: dict[str, str] = {}
    replaces: list[tuple[str, str, str]] = []

    for line in TRANSCRIPT.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("role") != "assistant":
            continue
        for item in obj.get("message", {}).get("content", []):
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("type")
            inp = item.get("input") or {}
            path = inp.get("path", "")
            if "multichain-wallet-core" not in path.replace("\\", "/").lower():
                continue
            rel = norm_path(path)
            if name == "Write":
                writes[rel] = inp.get("contents", "")
            elif name == "StrReplace":
                replaces.append((rel, inp.get("old_string", ""), inp.get("new_string", "")))

    return writes, replaces


def apply_replacements(content: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        content = content.replace(old, new)
    return content


def fix_folder_namespaces(content: str, folder: str) -> str:
    ns = FOLDER_NAMESPACE_FIXES.get(folder)
    if not ns:
        return content
    return re.sub(
        r"namespace McWallet\.Engine\.Orchestration;|namespace McWallet\.Cryptography\.Derivation;|"
        r"namespace McWallet\.ChainProviders\.Transport;|namespace McWallet\.Persistence\.Stores;|"
        r"namespace McWallet\.App;",
        f"namespace {ns};",
        content,
        count=1,
    )


def migrate_to_mcwallet(old_files: dict[str, str]) -> dict[str, str]:
    new_files: dict[str, str] = {}

    for src, dst in COPY_MAP:
        if src in old_files:
            new_files[dst] = old_files[src]

    for pattern, dest_dir in GLOB_COPY:
        prefix = pattern.split("/*.cs")[0] + "/"
        for rel, content in old_files.items():
            if rel.startswith(prefix) and rel.endswith(".cs"):
                name = Path(rel).name
                new_files[f"{dest_dir}/{name}"] = content

    # PortfolioReporter may live in Services
    if "src/MultiChainWallet.Core/Services/PortfolioReporter.cs" in old_files:
        new_files["src/Engine/Analytics/PortfolioReporter.cs"] = old_files[
            "src/MultiChainWallet.Core/Services/PortfolioReporter.cs"
        ]

    # HexConverter from Encoding folder
    for rel, content in old_files.items():
        if rel.startswith("src/MultiChainWallet.Crypto/Encoding/"):
            name = Path(rel).name
            new_files[f"src/Cryptography/Codecs/{name}"] = content

    # Root-level docs and config from writes
    for rel in (
        ".editorconfig",
        ".gitignore",
        "LICENSE",
        "docs/ARCHITECTURE.md",
        "docs/API.md",
        "docs/CONTRIBUTING.md",
    ):
        if rel in old_files:
            new_files[rel] = old_files[rel]

    return new_files


def post_process_files(files: dict[str, str]) -> None:
    folder_ns = {
        "src/Cryptography/Codecs/": "McWallet.Cryptography.Codecs",
        "src/Cryptography/Vault/": "McWallet.Cryptography.Vault",
        "src/Cryptography/Signing/": "McWallet.Cryptography.Signing",
        "src/Cryptography/Mnemonic/": "McWallet.Cryptography.Mnemonic",
        "src/Cryptography/Derivation/": "McWallet.Cryptography.Derivation",
        "src/Engine/Analytics/": "McWallet.Engine.Analytics",
        "src/Engine/Networks/": "McWallet.Engine.Networks",
        "src/ChainProviders/Evm/": "McWallet.ChainProviders.Evm",
        "src/ChainProviders/Utxo/": "McWallet.ChainProviders.Utxo",
        "src/Persistence/Schema/": "McWallet.Persistence.Schema",
    }

    for rel, content in list(files.items()):
        if not rel.endswith(".cs"):
            continue
        for prefix, ns in folder_ns.items():
            if rel.startswith(prefix):
                content = re.sub(r"namespace [^;]+;", f"namespace {ns};", content, count=1)
                content = content.replace("namespace MultiChainWallet.Crypto.Encoding;", f"namespace {ns};")
                files[rel] = content
                break

    for rel in list(files.keys()):
        if rel.endswith(".cs"):
            files[rel] = re.sub(r"(namespace [^;]+;\n)\1+", r"\1", files[rel])

    bip39 = files.get("src/Cryptography/Derivation/Bip39MnemonicProcessor.cs")
    if bip39:
        bip39 = re.sub(r": IKeyDerivationService", "", bip39)
        bip39 = re.sub(r"\n    private readonly Sha256Hasher _hasher;\n", "\n", bip39)
        bip39 = re.sub(
            r"public Bip39MnemonicProcessor\(Bip32KeyDeriver bip32, Sha256Hasher hasher\)\n    \{\n        _bip32 = bip32;\n        _hasher = hasher;\n    \}",
            "public Bip39MnemonicProcessor(Bip32KeyDeriver bip32)\n    {\n        _bip32 = bip32;\n    }",
            bip39,
        )
        files["src/Cryptography/Derivation/Bip39MnemonicProcessor.cs"] = bip39

    pr = files.get("src/Engine/Analytics/PortfolioReporter.cs") or files.get(
        "src/Engine/Orchestration/PortfolioReporter.cs"
    )
    if pr:
        pr = re.sub(r"namespace McWallet\.Engine\.Orchestration;", "namespace McWallet.Engine.Analytics;", pr, count=1)
        files["src/Engine/Analytics/PortfolioReporter.cs"] = pr
        files.pop("src/Engine/Orchestration/PortfolioReporter.cs", None)

    for rel in ("src/Engine/Orchestration/DefaultWalletProvider.cs", "src/Engine/Orchestration/WalletManager.cs"):
        if rel in files:
            seen: set[str] = set()
            lines = []
            for line in files[rel].splitlines():
                if line.startswith("using ") and line in seen:
                    continue
                if line.startswith("using "):
                    seen.add(line)
                lines.append(line)
            files[rel] = "\n".join(lines) + "\n"

    if "src/App/appsettings.json" not in files and "src/MultiChainWallet.Cli/appsettings.json" in files:
        files["src/App/appsettings.json"] = files["src/MultiChainWallet.Cli/appsettings.json"]


def main() -> None:
    writes, str_replaces = parse_transcript()
    print(f"Parsed {len(writes)} writes, {len(str_replaces)} str replacements")

    readme_backup = None
    readme_path = BASE / "README.md"
    if readme_path.exists():
        readme_backup = readme_path.read_text(encoding="utf-8")

    if BASE.exists():
        for child in BASE.iterdir():
            if child.name == "build":
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
    else:
        BASE.mkdir(parents=True)

    # Phase 1: build MultiChainWallet tree from transcript
    mcw: dict[str, str] = {}
    for rel, content in writes.items():
        if should_skip_output(rel):
            continue
        mcw[rel] = content

    # Phase 2: migrate to McWallet layout
    files = migrate_to_mcwallet(mcw)

    # Phase 3: apply namespace replacements
    for rel in list(files.keys()):
        if rel.endswith(".cs") or rel.endswith(".csproj"):
            files[rel] = apply_replacements(files[rel], NAMESPACE_REPLACEMENTS)

    for folder, _ in FOLDER_NAMESPACE_FIXES.items():
        prefix = folder + "/"
        for rel in list(files.keys()):
            if rel.startswith(prefix) and rel.endswith(".cs"):
                files[rel] = fix_folder_namespaces(files[rel], folder)

    # Phase 4: overlay McWallet-final writes from transcript
    for rel, content in writes.items():
        if should_skip_output(rel):
            continue
        if rel.startswith("src/App/") or rel.endswith(".slnx") or rel == "Directory.Build.props":
            files[rel] = content
        elif rel.endswith(".csproj") and any(
            rel.startswith(p) for p in ("src/App/", "src/Engine/", "src/Cryptography/", "src/ChainProviders/", "src/Persistence/", "tests/")
        ):
            files[rel] = content
        elif rel == "docs/STRUCTURE.md":
            files[rel] = content

    # Phase 5: apply StrReplace chain on final files
    for rel, old, new in str_replaces:
        if should_skip_output(rel):
            continue
        if rel not in files:
            continue
        if old and old in files[rel]:
            files[rel] = files[rel].replace(old, new, 1)

    # Phase 6: post-process namespaces and known fixes
    post_process_files(files)

    # NetworkRegistry local RPC hosts
    nr = "src/Engine/Networks/NetworkRegistry.cs"
    if nr in files:
        files[nr] = files[nr].replace("https://eth.llamarpc.com", "eth-mainnet.rpc.vault-labs.local:8545")
        files[nr] = files[nr].replace("https://rpc.ankr.com/eth", "eth-mainnet.rpc.vault-labs.local:8546")
        files[nr] = files[nr].replace("https://etherscan.io", "explorer.eth.vault-labs.local")
        files[nr] = files[nr].replace("https://blockstream.info/api", "btc-mainnet.rpc.vault-labs.local:8332")
        files[nr] = files[nr].replace("https://blockstream.info", "explorer.btc.vault-labs.local")
        files[nr] = files[nr].replace("https://polygon-rpc.com", "polygon-mainnet.rpc.vault-labs.local:8545")
        files[nr] = files[nr].replace("https://polygonscan.com", "explorer.polygon.vault-labs.local")
        files[nr] = files[nr].replace("https://bsc-dataseed.binance.org", "bsc-mainnet.rpc.vault-labs.local:8545")
        files[nr] = files[nr].replace("https://bscscan.com", "explorer.bsc.vault-labs.local")

    # Simulated RPC in EVM clients
    sim_block = """    public override async Task<long> GetLatestBlockNumberAsync(CancellationToken cancellationToken)
    {
        await Task.Yield();
        return 19_500_000 + (DateTime.UtcNow.Minute * 10);
    }

    public override async Task<decimal> GetNativeBalanceAsync(string address, CancellationToken cancellationToken)
    {
        await Task.Yield();
        return SimulateBalance(address);
    }"""
    for evm in (
        "src/ChainProviders/Evm/EthereumRpcClient.cs",
        "src/ChainProviders/Evm/PolygonRpcClient.cs",
        "src/ChainProviders/Evm/BscRpcClient.cs",
    ):
        if evm in files:
            files[evm] = re.sub(
                r"public override async Task<long> GetLatestBlockNumberAsync[\s\S]*?return SimulateBalance\(address\);\s*\}",
                sim_block,
                files[evm],
                count=1,
            )

    # Directory.Build.props final form
    files["Directory.Build.props"] = """<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
    <Authors>vault-labs</Authors>
    <Company>Vault Labs OSS</Company>
    <Product>MultiChain Wallet Core</Product>
    <Version>2.4.1</Version>
    <Copyright>Copyright (c) 2024-2026 Vault Labs</Copyright>

    <!-- All bin/obj output centralized under /build -->
    <UseArtifactsOutput>true</UseArtifactsOutput>
    <ArtifactsPath>$(MSBuildThisFileDirectory)build</ArtifactsPath>
  </PropertyGroup>
</Project>
"""

    files["multichain-wallet-core.slnx"] = """<Solution>
  <Folder Name="/src/">
    <Project Path="src/App/App.csproj" />
    <Project Path="src/Engine/Engine.csproj" />
    <Project Path="src/Cryptography/Cryptography.csproj" />
    <Project Path="src/ChainProviders/ChainProviders.csproj" />
    <Project Path="src/Persistence/Persistence.csproj" />
  </Folder>
  <Folder Name="/tests/">
    <Project Path="tests/Engine.Tests/Engine.Tests.csproj" />
    <Project Path="tests/Cryptography.Tests/Cryptography.Tests.csproj" />
  </Folder>
</Solution>
"""

    if readme_backup:
        files["README.md"] = readme_backup
    elif "README.md" in writes:
        files["README.md"] = writes["README.md"]

    # Write all files
    created: list[str] = []
    for rel, content in sorted(files.items()):
        if not content:
            continue
        target = BASE / rel.replace("/", "\\")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        created.append(rel.replace("\\", "/"))

    print(f"Created {len(created)} files under {BASE}")
    for f in created:
        print(f"  {f}")


if __name__ == "__main__":
    main()
