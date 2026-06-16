# Jellyfin-Plugins

`CursedCodeStudios/Jellyfin-Plugins` is a dedicated GitHub repository for publishing a Jellyfin plugin repository manifest. Instead of having each plugin repository edit a shared JSON file directly, this repository owns `manifest.json` and exposes a GitHub Actions workflow that plugin repositories can trigger after a release is published.

The public Jellyfin repository manifest URL is:

`https://raw.githubusercontent.com/CursedCodeStudios/Jellyfin-Plugins/main/manifest.json`

## Add This Repository To Jellyfin

In Jellyfin, go to `Dashboard -> Plugins -> Repositories -> Add` and use:

- Name: `CursedCodeStudios Jellyfin Plugin Repository`
- URL: `https://raw.githubusercontent.com/CursedCodeStudios/Jellyfin-Plugins/main/manifest.json`

## Repository Layout

- `manifest.json`: The published Jellyfin repository manifest. It starts as an empty JSON array.
- `scripts/update_manifest.py`: Standard-library-only helper for adding or updating plugin entries.
- `.github/workflows/update-plugin.yml`: GitHub Actions workflow that handles `repository_dispatch` and `workflow_dispatch`.
- `examples/continuum-dispatch-payload.json`: Example payload for `CursedCodeStudios/Jellyfin.Plugin.Continuum`.

## How Plugin Repositories Update The Manifest

Plugin repositories publish a release, compute the release checksum, and then trigger the `Update Plugin Manifest` workflow in `CursedCodeStudios/Jellyfin-Plugins`. The workflow reads the payload, updates the matching plugin entry by GUID, preserves all older versions, replaces any duplicate version entry, validates the JSON, and commits `manifest.json` back to this repository only if the manifest actually changed.

Top-level plugin metadata that is updated on each run:

- `guid`
- `name`
- `description`
- `overview`
- `owner`
- `category`

Each release version entry contains:

- `version`
- `changelog`
- `targetAbi`
- `sourceUrl`
- `checksum`
- `timestamp`
- `repositoryName`
- `repositoryUrl`
- `url`

Versions are sorted in descending dotted numeric order, and plugin entries are sorted alphabetically by plugin name.

## Payload Fields

Required payload fields:

- `pluginGuid`
- `pluginName`
- `version`
- `targetAbi`
- `checksum`
- `sourceUrl`
- `repositoryUrl`
- `url`

Optional payload fields:

- `description`
- `overview`
- `owner`
- `category`
- `changelog`
- `repositoryName`
- `repositoryUrl` when using `workflow_dispatch`
- `timestamp`

Default values when optional fields are omitted:

- `description`: `""`
- `overview`: Same value as `description`
- `owner`: `CursedCodeStudios`
- `category`: `General`
- `changelog`: `Release {version}.`
- `repositoryName`: `CursedCodeStudios Jellyfin Plugin Repository`
- `timestamp`: Current UTC time in ISO-8601 format

## Trigger From Another Repository With `repository_dispatch`

Store a token named `MANIFEST_REPO_TOKEN` in the plugin repository that will send the dispatch. Do not store this token in the manifest repository.

The token should be a fine-grained GitHub token scoped to:

- Repository: `CursedCodeStudios/Jellyfin-Plugins`
- Permission level: whatever GitHub currently requires to trigger workflow or `repository_dispatch` events for that repository

Example request from `CursedCodeStudios/Jellyfin.Plugin.Continuum`:

```bash
curl -X POST \
  -H "Authorization: Bearer ${MANIFEST_REPO_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/CursedCodeStudios/Jellyfin-Plugins/dispatches \
  -d '{
    "event_type": "update-plugin-release",
    "client_payload": {
      "pluginGuid": "PLUGIN-GUID-HERE",
      "pluginName": "Continuum",
      "description": "Creates rolling per-user playlists from manually ordered movie and episode lists.",
      "overview": "Continuum turns manually maintained chronological or canonical watch orders into per-user rolling Jellyfin playlists.",
      "owner": "CursedCodeStudios",
      "category": "General",
      "version": "0.1.0.0",
      "targetAbi": "10.11.0.0",
      "checksum": "SHA256_CHECKSUM_HERE",
      "timestamp": "2026-01-01T00:00:00Z",
      "sourceUrl": "https://github.com/CursedCodeStudios/Jellyfin.Plugin.Continuum",
      "changelog": "Initial release.",
      "repositoryName": "CursedCodeStudios Jellyfin Plugin Repository",
      "repositoryUrl": "https://raw.githubusercontent.com/CursedCodeStudios/Jellyfin-Plugins/main/manifest.json",
      "url": "https://github.com/CursedCodeStudios/Jellyfin.Plugin.Continuum/releases/download/v0.1.0.0/Jellyfin.Plugin.Continuum_0.1.0.0.zip"
    }
  }'
```

See [examples/continuum-dispatch-payload.json](/Volumes/Vault/Projects/CursedCode/Jellyfin-Plugins/examples/continuum-dispatch-payload.json) for the same payload in a reusable file.

## Manually Trigger The Workflow With `workflow_dispatch`

You can run the workflow manually from the GitHub Actions UI by selecting `Update Plugin Manifest` and filling in the workflow inputs.

You can also use the GitHub CLI:

```bash
gh workflow run update-plugin.yml \
  --repo CursedCodeStudios/Jellyfin-Plugins \
  -f pluginGuid=PLUGIN-GUID-HERE \
  -f pluginName=Continuum \
  -f version=0.1.0.0 \
  -f targetAbi=10.11.0.0 \
  -f checksum=SHA256_CHECKSUM_HERE \
  -f sourceUrl=https://github.com/CursedCodeStudios/Jellyfin.Plugin.Continuum \
  -f url=https://github.com/CursedCodeStudios/Jellyfin.Plugin.Continuum/releases/download/v0.1.0.0/Jellyfin.Plugin.Continuum_0.1.0.0.zip \
  -f description='Creates rolling per-user playlists from manually ordered movie and episode lists.' \
  -f overview='Continuum turns manually maintained chronological or canonical watch orders into per-user rolling Jellyfin playlists.' \
  -f owner=CursedCodeStudios \
  -f category=General \
  -f changelog='Initial release.' \
  -f repositoryName='CursedCodeStudios Jellyfin Plugin Repository' \
  -f repositoryUrl=https://raw.githubusercontent.com/CursedCodeStudios/Jellyfin-Plugins/main/manifest.json
```

If you omit optional workflow inputs, the script fills in the documented defaults.

For manual runs, `repositoryUrl` defaults to `https://raw.githubusercontent.com/CursedCodeStudios/Jellyfin-Plugins/main/manifest.json` when left blank.

## Validate The Manifest Locally

```bash
python -m json.tool manifest.json
```

## Run The Update Script Locally

Example local invocation:

```bash
python scripts/update_manifest.py \
  --manifest-path manifest.json \
  --plugin-guid "PLUGIN-GUID-HERE" \
  --plugin-name "Continuum" \
  --description "Creates rolling per-user playlists from manually ordered movie and episode lists." \
  --overview "Continuum turns manually maintained chronological or canonical watch orders into per-user rolling Jellyfin playlists." \
  --owner "CursedCodeStudios" \
  --category "General" \
  --version "0.1.0.0" \
  --target-abi "10.11.0.0" \
  --checksum "SHA256_CHECKSUM_HERE" \
  --timestamp "2026-01-01T00:00:00Z" \
  --source-url "https://github.com/CursedCodeStudios/Jellyfin.Plugin.Continuum" \
  --changelog "Initial release." \
  --repository-name "CursedCodeStudios Jellyfin Plugin Repository" \
  --repository-url "https://raw.githubusercontent.com/CursedCodeStudios/Jellyfin-Plugins/main/manifest.json" \
  --url "https://github.com/CursedCodeStudios/Jellyfin.Plugin.Continuum/releases/download/v0.1.0.0/Jellyfin.Plugin.Continuum_0.1.0.0.zip"
```

## Local Safety Notes

- No tokens are hardcoded in this repository.
- The updater does not remove other plugins from the manifest.
- The updater does not remove older versions of a plugin.
- Duplicate version entries are replaced instead of duplicated.
- The updater uses only the Python standard library.
- Missing required fields cause a clear error.
- Missing optional fields fall back to safe defaults.
