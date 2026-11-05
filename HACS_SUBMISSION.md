# HACS Submission

How to get this integration into the HACS **default store**, i.e. visible to every user without
adding the repository URL by hand. Everything below is taken from the current HACS documentation
(<https://hacs.xyz/docs/publish/include/> and <https://hacs.xyz/docs/publish/integration/>) and
verified against this repository.

## Repository Information

- **Repository URL:** https://github.com/thcuba/homeassistant-koolnova
- **Category:** Integration
- **Integration type:** hub (cloud polling)
- **Minimum Home Assistant:** 2025.12.0 (as declared in `hacs.json`)
- **Country:** Spain and Italy (`"country": ["ES", "IT"]`)
- **License:** MIT

## Requirements and current state

| Requirement | State |
|---|---|
| Public GitHub repository with a description and a README | ✅ |
| Repository topics (for searchability) | ✅ includes `hacs` |
| `hacs.json` in the repository root with at least `name` | ✅ |
| One integration only, all files under `custom_components/koolnova/` | ✅ |
| `manifest.json` with `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version` | ✅ |
| Brand assets in the repository — `custom_components/koolnova/brand/icon.png` | ✅ |
| `hassfest` passing | ✅ |
| **HACS Action passing with no errors and no `ignore:`** | ❌ the workflow passes `ignore: brands` |
| A **full GitHub release** (not just a tag) after the checks are green | ✅ `2.0.10` |
| PR opened by the owner or a major contributor, and editable (not from an organization account) | ✅ `@thcuba` is the owner |

The only open item is `ignore: brands` in `.github/workflows/validate.yml`. It is harmless for a
*custom repository* (that is how this repo is installed today), but the HACS Action has to pass
**without ignores** to be accepted as a default. Removing it works because the brand assets are
inside the package: the check used to fall back to `home-assistant/brands`, which no longer accepts
custom integrations.

## How to submit

1. Create a **new branch from `master`** in your fork of
   [hacs/default](https://github.com/hacs/default) — do not commit on `master`.
2. Edit the file **`integration`** (not `integrations.json`). It is a JSON array of `"owner/repo"`
   strings, one per line, kept in alphabetical order. Add:

   ```json
   "thcuba/homeassistant-koolnova",
   ```

   in the right alphabetical position, not at the end.
3. Open the pull request and fill in the template **completely**. Incomplete or misrepresenting
   PRs are closed without notice.
4. Wait for review. New additions are processed in batches and can take months.

Rules worth knowing before opening the PR:

- Only the owner or a major contributor of the repository may submit it.
- Custom integrations that override a core integration, or that exist only for alpha/beta testing,
  are not accepted as defaults (they can still be used as custom repositories).
- The repository must not be archived, and it must have a license.
- Once merged, the repository is picked up by the next scheduled scan.

## Pre-submission check (local)

```bash
python3 -m json.tool custom_components/koolnova/manifest.json   # valid manifest
python3 -m json.tool hacs.json                                  # valid hacs.json
ls custom_components/koolnova/brand/icon.png                    # brand inside the package
python3 scripts/check_version.py --not-older-than $(git tag --sort=-creatordate | head -1)
```

## Attribution

- **Original creator:** [@luisgsluis](https://github.com/luisgsluis)
- **Current maintainer:** [@thcuba](https://github.com/thcuba)

## Resources

- [HACS — include default repositories](https://hacs.xyz/docs/publish/include/)
- [HACS — integration requirements](https://hacs.xyz/docs/publish/integration/)
- [Home Assistant — integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest)
