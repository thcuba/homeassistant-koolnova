# HACS Submission Template

This document provides a template for submitting the Koolnova Home Assistant integration to HACS.

## 📝 Pull Request Template for HACS

When submitting to the [hacs/default](https://github.com/hacs/default) repository, use the following information:

### Repository Information
- **Repository URL:** https://github.com/thcuba/homeassistant-koolnova
- **Category:** Integration
- **Integration Type:** hub (cloud polling)
- **Target Home Assistant Version:** 2024.12.0+

### What This Integration Does

The Koolnova Home Assistant integration provides full control of Koolnova HVAC climate control systems via the Koolnova REST API. Users can manage:
- Per-zone temperature control
- HVAC mode selection (COOL / HEAT / AUTO / OFF)
- Fan speed adjustment
- Global project-level controls
- Real-time sensor updates with smart polling

### Key Features
- ✅ Config flow UI integration
- ✅ Manifest validation ready
- ✅ MIT Licensed
- ✅ Full documentation included
- ✅ Active maintenance
- ✅ GitHub issue tracking

### Repository Structure
```
homeassistant-koolnova/
├── custom_components/koolnova/    # Main integration code
│   ├── manifest.json               # Integration metadata
│   ├── __init__.py                 # Core integration
│   ├── config_flow.py              # Configuration UI
│   └── [other component files]
├── docs/                           # Documentation
│   ├── ARCHITECTURE.md             # Architecture details
│   ├── API.md                      # Koolnova API reference
│   ├── DEV_ENV.md                  # Development setup
│   ├── TROUBLESHOOTING.md          # Troubleshooting guide
│   └── RELEASE.md                  # Release notes
├── brand/                          # Brand assets
├── tests/                          # Test suite
├── hacs.json                       # HACS configuration
├── icon.png                        # Integration icon
└── README.md                       # Main documentation
```

### Validation Checklist
- ✅ Repository is public
- ✅ MIT License included
- ✅ hacs.json properly configured
- ✅ manifest.json in custom_components/koolnova/
- ✅ config_flow.py implemented
- ✅ Integration icon (icon.png) provided
- ✅ README with installation instructions
- ✅ Complete documentation in docs/

### Testing & Quality
- ✅ HACS validation workflow configured
- ✅ Integration passes HACS validation
- ✅ No blocking issues or security concerns
- ✅ Active maintenance and support

### Original Creator Attribution
- **Original Creator:** [@luisgsluis](https://github.com/luisgsluis)
- **Current Maintainer:** [@thcuba](https://github.com/thcuba)

---

## 🚀 Steps to Submit

1. **Fork** the [hacs/default](https://github.com/hacs/default) repository
2. **Edit** the `integrations.json` file
3. **Add** an entry for the Koolnova integration following the existing format:
   ```json
   {
     "domain": "koolnova",
     "name": "Koolnova",
     "documentation": "https://github.com/thcuba/homeassistant-koolnova",
     "homeassistant": "2024.12.0",
     "iot_class": "cloud_polling",
     "issue_tracker": "https://github.com/thcuba/homeassistant-koolnova/issues",
     "requirements": ["requests"],
     "country": ["IT"]
   }
   ```
4. **Create** a Pull Request with title: `Add Koolnova integration`
5. **Wait** for HACS maintainers to review and merge

## ✅ Pre-Submission Verification

Run these checks before submitting:

```bash
# Clone the repository
git clone https://github.com/thcuba/homeassistant-koolnova
cd homeassistant-koolnova

# Verify file structure
ls -la custom_components/koolnova/manifest.json
ls -la hacs.json
ls -la icon.png

# Check JSON validity
python3 -m json.tool custom_components/koolnova/manifest.json
python3 -m json.tool hacs.json
```

## 📚 Additional Resources

- [HACS Integration Documentation](https://hacs.xyz/docs/publish/integration)
- [Home Assistant Integration Requirements](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Manifest Documentation](https://developers.home-assistant.io/docs/creating_component_manifest/)

---

**Status:** Ready for HACS submission ✅
