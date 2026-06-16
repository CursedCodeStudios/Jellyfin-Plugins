#!/usr/bin/env python3

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ManifestError(Exception):
    """Raised when the manifest file is malformed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add or update a plugin entry in a Jellyfin repository manifest."
    )
    parser.add_argument("--manifest-path", required=True)
    parser.add_argument("--plugin-guid", required=True)
    parser.add_argument("--plugin-name", required=True)
    parser.add_argument("--description")
    parser.add_argument("--overview")
    parser.add_argument("--owner")
    parser.add_argument("--category")
    parser.add_argument("--version", required=True)
    parser.add_argument("--target-abi", required=True)
    parser.add_argument("--checksum", required=True)
    parser.add_argument("--timestamp")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--changelog")
    parser.add_argument("--repository-name")
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--url", required=True)
    return parser.parse_args()


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def require_value(name: str, value: str | None) -> str:
    normalized = normalize_optional(value)
    if normalized is None:
        raise ValueError(f"--{name} is required and cannot be empty.")
    return normalized


def utc_now_iso8601() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Failed to parse {path}: {exc}") from exc

    if not isinstance(data, list):
        raise ManifestError(f"Manifest root must be a JSON array in {path}.")

    for index, plugin in enumerate(data):
        if not isinstance(plugin, dict):
            raise ManifestError(f"Manifest entry at index {index} must be a JSON object.")

    return data


def parse_version_key(version: str) -> tuple[int, ...]:
    parts = version.split(".")
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"Invalid dotted numeric version: {version}")

    numeric_parts = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"Invalid dotted numeric version: {version}")
        numeric_parts.append(int(part))
    return tuple(numeric_parts)


def sort_plugins(manifest: list[dict[str, Any]]) -> None:
    manifest.sort(key=lambda item: str(item.get("name", item.get("guid", ""))).casefold())


def main() -> int:
    args = parse_args()

    manifest_path = Path(require_value("manifest-path", args.manifest_path))
    plugin_guid = require_value("plugin-guid", args.plugin_guid)
    plugin_name = require_value("plugin-name", args.plugin_name)
    version = require_value("version", args.version)
    target_abi = require_value("target-abi", args.target_abi)
    checksum = require_value("checksum", args.checksum)
    source_url = require_value("source-url", args.source_url)
    repository_url = require_value("repository-url", args.repository_url)
    download_url = require_value("url", args.url)

    description = normalize_optional(args.description) or ""
    overview = normalize_optional(args.overview) or description
    owner = normalize_optional(args.owner) or "CursedCodeStudios"
    category = normalize_optional(args.category) or "General"
    changelog = normalize_optional(args.changelog) or f"Release {version}."
    repository_name = (
        normalize_optional(args.repository_name)
        or "CursedCodeStudios Jellyfin Plugin Repository"
    )
    timestamp = normalize_optional(args.timestamp) or utc_now_iso8601()

    manifest = load_manifest(manifest_path)
    previous_manifest = copy.deepcopy(manifest)

    plugin_entry = next((item for item in manifest if item.get("guid") == plugin_guid), None)
    created_plugin = plugin_entry is None
    if plugin_entry is None:
        plugin_entry = {"guid": plugin_guid, "versions": []}
        manifest.append(plugin_entry)

    plugin_entry["guid"] = plugin_guid
    plugin_entry["name"] = plugin_name
    plugin_entry["description"] = description
    plugin_entry["overview"] = overview
    plugin_entry["owner"] = owner
    plugin_entry["category"] = category

    versions = plugin_entry.get("versions")
    if versions is None:
        versions = []
    elif not isinstance(versions, list):
        raise ManifestError(f"Plugin '{plugin_guid}' has a non-array 'versions' field.")

    for index, item in enumerate(versions):
        if not isinstance(item, dict):
            raise ManifestError(
                f"Plugin '{plugin_guid}' has a non-object version entry at index {index}."
            )

    replaced_version = any(item.get("version") == version for item in versions)
    filtered_versions = [item for item in versions if item.get("version") != version]
    filtered_versions.append(
        {
            "version": version,
            "changelog": changelog,
            "targetAbi": target_abi,
            "sourceUrl": source_url,
            "checksum": checksum,
            "timestamp": timestamp,
            "repositoryName": repository_name,
            "repositoryUrl": repository_url,
            "url": download_url,
        }
    )
    filtered_versions.sort(key=lambda item: parse_version_key(str(item["version"])), reverse=True)
    plugin_entry["versions"] = filtered_versions

    sort_plugins(manifest)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if manifest == previous_manifest:
        print(
            f"No manifest changes for {plugin_name} {version}. "
            f"Plugin count: {len(manifest)}."
        )
    else:
        action = "Created" if created_plugin else "Updated"
        version_action = "replaced" if replaced_version else "added"
        print(
            f"{action} plugin '{plugin_name}' ({plugin_guid}); "
            f"{version_action} version {version}; "
            f"plugin count: {len(manifest)}."
        )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ManifestError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}")
