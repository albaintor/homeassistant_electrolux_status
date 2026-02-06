# Release Notes - v3.0.0

## 🚨 BREAKING CHANGES 🚨

**This release contains BREAKING CHANGES that require user action!**

## 🎯 **MAJOR UPGRADE: Official Electrolux API**

**MOVED FROM UNMAINTAINED THIRD-PARTY LIBRARY TO OFFICIAL ELECTROLUX API!**

- ❌ **REMOVED**: Unmaintained `pyelectroluxocp` library ([deprecated](https://github.com/Woyten/py-electrolux-ocp))
- ✅ **NEW**: Official [`electrolux-group-developer-sdk`](https://github.com/electrolux-oss/electrolux-group-developer-sdk) with full Electrolux support
- **Result**: Reliable, secure, and future-proof integration

This is a complete refactor of the Electrolux integration to use the official Electrolux Group Developer API. The legacy username/password authentication has been removed and replaced with official API key authentication.

### ⚠️ Critical Changes

#### 1. **Authentication Method Changed**
- ❌ **REMOVED**: Username/password authentication no longer supported
- ✅ **NEW**: API key, access token, and refresh token required
- **Action Required**: Obtain credentials from [Electrolux Developer Portal](https://developer.electrolux.one/dashboard)

#### 2. **Entity IDs Will Change**
- All entity IDs will be different after migration
- **Action Required**: Update automations, scripts, and dashboards
- **Recommendation**: Consider using device-based automations for future compatibility

#### 3. **Model Display Changed**
- Appliances now show Product Number Codes (PNC) instead of marketing names
- Example: "944188772" instead of "BSE788380M"
- This provides more specific identification

### 🔄 Migration Required

**Complete migration guide available in the [README](README.md#migration-guide-upgrading-from-legacy-authentication)**

Key migration steps:
1. Backup your current configuration
2. Obtain new API credentials from developer portal
3. Remove old integration
4. Install new version
5. Reconfigure with new credentials
6. Update automations/scripts with new entity IDs

### ✅ Major Improvements

- **Official API Integration**: Uses official [`electrolux-group-developer-sdk`](https://github.com/electrolux-oss/electrolux-group-developer-sdk) instead of unmaintained third-party libraries
- **Real-time Updates**: Server-Sent Events (SSE) instead of polling
- **Enhanced Security**: Token-based authentication with auto-refresh
- **Better Reliability**: Comprehensive error handling and connection management
- **Safety Validations**: Remote control respects appliance safety locks
- **More Sensors**: Additional diagnostic and status information

### 📋 Compatibility

- **Home Assistant**: Requires modern Home Assistant (async patterns)
- **Appliances**: All Electrolux and Electrolux-owned brands (AEG, Frigidaire, Husqvarna)
- **Regions**: EMEA, APAC, LATAM, NA supported

### 🐛 Known Issues

- Entity IDs change during migration (expected)
- Some appliance features may vary by region/model
- Real-time updates depend on appliance connectivity

### 📖 Documentation

For complete documentation including:
- Detailed migration guide
- API credential setup
- Troubleshooting
- Feature overview

See the [README.md](README.md)

### 🙏 Credits

- **Refactored by**: [TTLucian](https://github.com/TTLucian)
- **Original Creators**: [albaintor](https://github.com/albaintor), [kingy444](https://github.com/kingy444)

---

**⚠️ IMPORTANT**: Test the migration in a development environment first. Backup your Home Assistant configuration before upgrading in production.</content>
<parameter name="filePath">RELEASE_NOTES_v3.0.0.md