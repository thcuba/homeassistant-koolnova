# Koolnova Integration Release Process

## Versioning

Versions are managed in `manifest.json`.

### Version Scheme
- **MAJOR**: Incompatible API or feature changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Bug fixes and minor improvements

## Git Tags

Create tags for each release following semantic versioning.

## HACS Compatibility

This integration is HACS (Home Assistant Community Store) compatible:

- **Type**: Integration
- **Installation method**: GitHub release (standard GitHub releases)
- **Repository URL**: https://github.com/thcuba/homeassistant-koolnova

### HACS Requirements

What HACS actually checks, per the current documentation:

- **Structure**: one integration only, everything under `custom_components/koolnova/`
- **`manifest.json`** with `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version`
- **`hacs.json`** in the repository root, at least `name`
- **Brand assets inside the repository**: `custom_components/koolnova/brand/icon.png`.
  `home-assistant/brands` no longer accepts custom integrations, so the brand lives here
- **HACS Action** (`hacs/action`, `category: integration`) passing with **no errors and no `ignore:`**.
  A custom repository may ignore `brands`; to be listed in the `hacs/default` store it may not
- **hassfest** passing
- **A full GitHub release** (not just a tag) created after those checks are green
- Translation files in `translations/` (optional)

### Required HACS Configuration (`hacs.json`)

The `hacs.json` file should include the following fields:

```json
{
  "name": "Koolnova",
  "homeassistant": "2025.12.0",
  "country": ["ES", "IT"]
}
```

**Critical fields**:
- `"homeassistant"`: Minimum compatible version.
- `"country"`: List of countries where the integration is relevant.

## Changelog

Release notes live in [CHANGELOG.md](../CHANGELOG.md). This section used to keep a second copy of
old entries and had gone stale, so it now just points there.

## Release Process

### ⚠️ CRITICAL: HACS-Compatible Structure

**HACS requires standard GitHub structure, NOT custom ZIPs**

### 📁 Required Directory Structure

```
REPOSITORY_ROOT/
├── custom_components/
│   └── koolnova/          ← Domain name
│       ├── __init__.py
│       ├── manifest.json  ← Version MUST match tag
│       ├── climate.py
│       └── ... (all integration files)
├── README.md              ← Root documentation
└── hacs.json              ← HACS config in root
```

### 🔧 Required HACS Configuration (`hacs.json`)

```json
{
  "name": "Koolnova",
  "homeassistant": "2025.12.0",
  "country": ["ES", "IT"]
}
```

**Note**: Do not include `domain`, `repository`, `categories`, or `zip_release` in `hacs.json` as they are either redundant or invalid for integrations and can cause CI failures.

### Steps for HACS-Compatible Release

1. **Development**: Implement changes in a feature branch
2. **Testing**: Verify functionality in Home Assistant
3. **Update JSON files**:
   - `manifest.json`: Set `"version"` to match upcoming tag (e.g., `v1.2.1` → `"version": "1.2.1"`)
   - `hacs.json`: check `name`, `homeassistant` and `country` (do **not** add `domain`, see the note above: the `hacsjson` check rejects it)
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a X.Y.Z -m "X.Y.Z"` — no `v` prefix, tags are `2.0.10`, `2.0.9`, ...
6. **Push**: `git push origin main --tags`
7. **Create GitHub Release**: Use GitHub UI (no custom workflows needed)
8. **HACS**: Users can now update via HACS

### 🎯 Key HACS Requirements

- **Structure**: Standard GitHub (`repository-version/custom_components/domain/...`)
- **Required files**:
  - `custom_components/koolnova/manifest.json` (correct version)
  - `hacs.json` (root configuration)
  - `README.md` (root documentation)
- **Versions**: Tag and `manifest.json` MUST be identical
- **Releases**: Standard GitHub releases (no custom assets)

### ❌ Common Error: Version Mismatch

**PROBLEM**: If `manifest.json` does not match the tag, HACS shows:
```
Downloading <owner>/<repository> with version X.Y.Z failed with (No content to download)
```

**PROBLEM 2**: HACS keeps offering the same update. It reads `manifest.json` to decide whether an
update is available, so if the manifest is behind while the tags move on it installs the release,
still sees the old version declared, and proposes the update again - forever.

**SOLUTION**: Ensure that:
- the tag is `2.0.11`
- `manifest.json` has `"version": "2.0.11"`
- they are exactly identical (no prefix/suffix)

**Enforced automatically**: `scripts/check_version.py`, run by the `Release version` workflow. A
pushed tag whose `manifest.json` disagrees fails the build, and a pull request whose manifest has
fallen behind the newest tag fails too - so the drift cannot go unnoticed again. Both checks run
locally as well:

```bash
python scripts/check_version.py --tag 2.0.9                        # a release about to be tagged
python scripts/check_version.py --not-older-than $(git tag --sort=-creatordate | head -1)
```

## Re-cutting a release (same version)

If a release has to be republished on a newer commit — for example when the manifest was wrong in
the release that went out — the tag moves and the release is recreated with the same notes:

```bash
git tag -f 2.0.10 <commit>                     # move the tag onto the new commit
git push --force origin refs/tags/2.0.10
gh release delete 2.0.10 --yes                  # the tag is kept
gh release create 2.0.10 --title 2.0.10 --notes-file <notes>
```

Save the existing notes first (`gh api repos/<owner>/<repo>/releases/tags/2.0.10 --jq .body`) or the
release changelog is lost. HACS caches what it downloaded: users who already installed that version
have to reinstall to get the corrected files.

## Distribution source

This repository is the single source of distribution for the integration. A second copy of the same
package must not be published: HACS keys an installation to the repository it came from, and the
default store expects one repository per domain — so a duplicate means two sources for
`custom_components/koolnova`, and installs that stop receiving updates as soon as one copy is
retired.

## Distribution

- **HACS**: Automatic updates
- **Manual**: Download from GitHub releases
- **Beta**: Use `dev` branch for testing

## Pre-Release Checklist

- [ ] All changes tested in Home Assistant
- [ ] `manifest.json` version matches upcoming tag (`python scripts/check_version.py --tag <tag>`)
- [ ] `hacs.json` configured correctly
- [ ] `custom_components/` directory present
- [ ] All imports use relative syntax (development rule check)
- [ ] No PyPI dependencies except HA core
- [ ] Documentation updated
- [ ] CHANGELOG entry added