# Home Assistant Electrolux Status Integration

[![Validate with HACS](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hacs.yml/badge.svg)](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hacs.yml)
[![Validate with hassfest](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hassfest.yml/badge.svg)](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hassfest.yml)

## Description

A comprehensive Home Assistant integration for Electrolux appliances using the official Electrolux Group Developer API. This integration provides real-time monitoring and control of Electrolux and Electrolux-owned brand appliances including AEG, Frigidaire, and Husqvarna.

**Key Features:**
- ✅ Real-time appliance status updates via Server-Sent Events (SSE)
- ✅ Remote control with safety validation (respects appliance safety locks)
- ✅ Automatic model detection from Product Number Codes (PNC)
- ✅ Comprehensive sensor coverage (temperatures, states, diagnostics)
- ✅ Control entities (buttons, switches, numbers, selects)
- ✅ Multi-language support
- ✅ Robust error handling and connection management

**Disclaimer:** This Home Assistant integration was not made by Electrolux. It is not official, not developed, and not supported by Electrolux.

## 🚨 USER TESTING NEEDED 🚨

**This integration has been completely refactored with major improvements!** We need your help testing with different appliances and regions to ensure everything works correctly.

### What Changed:
- ✅ Migrated to official Electrolux Group Developer API
- ✅ Real-time updates via Server-Sent Events (SSE)
- ✅ Enhanced safety validations for remote control
- ✅ Improved model detection from Product Number Codes (PNC)
- ✅ Better error handling and connection management

### How to Help:
1. **Test with your appliances** - Try the integration with different device types (ovens, washers, fridges, etc.)
2. **Report issues** - If something doesn't work, [create an issue](https://github.com/albaintor/homeassistant_electrolux_status/issues) with details
3. **Share your experience** - Let us know which appliances work well in the [discussions](https://github.com/albaintor/homeassistant_electrolux_status/discussions)
4. **Test in different regions** - Help verify compatibility across EMEA, APAC, LATAM, and NA

**Your feedback is crucial** to ensure the integration works reliably for everyone!

## Credits & History

**Refactored by [TTLucian](https://github.com/TTLucian)**

**Original Creators:**
- **[albaintor](https://github.com/albaintor)** - Original integration development
- **[kingy444](https://github.com/kingy444)** - Major contributions and maintenance

**Complete Refactoring (2026):**
This integration has been completely refactored to use the official Electrolux Group Developer API instead of the legacy authentication methods. The refactoring includes:
- **Removed dependency on deprecated pyelectroluxocp** ([https://github.com/Woyken/py-electrolux-ocp](https://github.com/Woyken/py-electrolux-ocp)) - now uses official Electrolux SDK
- Migration from username/password to API key authentication
- Implementation of real-time SSE streaming
- Enhanced model detection and device identification
- Comprehensive error handling and safety validations
- Modern async/await patterns and improved code architecture

| Contributors | Support Link |
|-------------|-------------|
| [albaintor](https://github.com/albaintor) | [!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/albaintor) |
| [kingy444](https://github.com/kingy444) | [!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/kingy444) |
| [TTLucian](https://github.com/TTLucian) | [!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/TTLucian) |

## Prerequisites

### API Credentials Required

This integration requires API credentials from the official Electrolux Developer Portal. **Username/password authentication is no longer supported.**

**Note:** Unfortunately, the official Electrolux API does not support direct username/password authentication. API access requires developer credentials obtained through their official developer portal.

#### How to Obtain API Credentials:

1. Visit the [Electrolux Developer Portal](https://developer.electrolux.one/dashboard)
2. Create a free developer account
3. Register a new application
4. Generate your API credentials:
   - **API Key** (Client ID)
   - **Access Token**
   - **Refresh Token**

**Important:** Keep your API credentials secure and never share them publicly.

## Migration Guide: Upgrading from Legacy Authentication

**⚠️ IMPORTANT:** This version completely replaces the old username/password authentication with official Electrolux API keys. The legacy authentication method is no longer supported.

### Why Migration is Required

The previous version relied on unofficial authentication methods that Electrolux has deprecated. This new version uses the official Electrolux Group Developer API, providing:
- ✅ Official support and reliability
- ✅ Real-time updates via Server-Sent Events
- ✅ Enhanced security and stability
- ✅ Better error handling and diagnostics

### What Changed

| Aspect | Old Version | New Version |
|--------|-------------|-------------|
| **Authentication** | Username/Password | API Key + Access Token + Refresh Token |
| **Updates** | Polling every 30 seconds | Real-time SSE streaming |
| **Model Display** | Marketing names (e.g., "BSE788380M") | Product codes (e.g., "944188772") |
| **Dependencies** | Unofficial `pyelectroluxocp` library | Official `electrolux_group_developer_sdk` |
| **Security** | Basic authentication | Token-based with automatic refresh |
| **Error Handling** | Limited error reporting | Comprehensive error handling |

### Step-by-Step Migration Process

#### Step 1: Backup Your Current Configuration
1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Find your existing Electrolux integration
3. Note down your appliance names and any custom configurations
4. **Do not delete the integration yet** - keep it running as backup

#### Step 2: Obtain New API Credentials
1. Visit the [Electrolux Developer Portal](https://developer.electrolux.one/dashboard)
2. Create a free developer account (use a different email if possible)
3. Register a new application:
   - **Application Name**: `Home Assistant Integration` (or any name you prefer)
   - **Description**: `Integration for Home Assistant`
4. Generate your API credentials:
   - **API Key** (Client ID) - save this
   - **Access Token** - save this
   - **Refresh Token** - save this
5. **Important**: Keep these credentials secure and never share them

#### Step 3: Remove Old Integration
1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Find your existing Electrolux integration
3. Click the integration and select **Delete**
4. Confirm deletion

#### Step 4: Install New Version
1. Update to this new version via HACS or manual installation
2. Restart Home Assistant

#### Step 5: Configure New Integration
1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Electrolux Status"
4. Enter your new API credentials:
   - API Key
   - Access Token  
   - Refresh Token
5. Click **Submit**

#### Step 6: Verify Migration
1. The integration should automatically discover your appliances
2. Check that all your appliances appear in Home Assistant
3. Verify that sensors and controls are working
4. Test a few basic functions (power on/off, temperature monitoring)

### What to Expect After Migration

#### ✅ Improvements
- **Faster Updates**: Real-time updates instead of 30-second polling
- **Better Reliability**: Official API with proper error handling
- **Enhanced Security**: Token-based authentication with auto-refresh
- **More Sensors**: Additional diagnostic and status information

#### ⚠️ Changes to Note
- **Model Names**: Appliances now show product codes (e.g., "944188772") instead of marketing names
- **New Entities**: Some sensors/controls may have different names or additional options
- **Connection Status**: Better visibility into appliance connectivity
- **Error Messages**: More detailed error reporting for troubleshooting
- **Entity IDs Change**: All entity IDs will be different after migration. Automations, scripts, and dashboards referencing old entity IDs will need updating.

#### 🔄 Same Functionality
- All your appliances should still be discovered
- Basic controls (power, temperature, programs) work the same
- Device history and settings are preserved (devices are matched by Product Number Code)

#### ⚠️ Actions Required After Migration
- **Update Automations**: Any automations using entity IDs will need to be updated with new entity IDs
- **Update Scripts**: Python scripts referencing entity IDs need updating
- **Update Dashboards**: Lovelace cards using entity IDs need updating
- **Consider Device-Based Automations**: Use device triggers/actions instead of entity-based ones for better future compatibility

### Troubleshooting Migration Issues

#### "No Appliances Found"
- Verify appliances are connected to your Electrolux account via the mobile app
- Check that appliances are powered on and connected to internet
- Try logging out/in of the Electrolux mobile app
- Wait 5-10 minutes and try reconfiguring the integration

#### "Authentication Failed"
- Double-check all three API credentials are entered correctly
- Regenerate tokens from the developer portal if needed
- Ensure you're using the correct regional Electrolux account

#### "Appliance Shows as Numbers"
- This is expected - the API provides product codes, not marketing names
- The product code is actually more specific and useful for identification

#### Old Integration Won't Delete
- Restart Home Assistant and try again
- Check Home Assistant logs for any error messages
- As last resort, manually edit `configuration.yaml` to remove any references

### Rollback Plan

If migration fails and you need to rollback:
1. The old integration code may still be available in HACS history
2. You can temporarily use the old username/password method
3. Contact the maintainers for support with migration issues

### Need Help?

- **Check the troubleshooting section** below for common issues
- **Test scripts** are available in the repository root for API testing
- **GitHub Issues**: Report problems with detailed error logs
- **GitHub Discussions**: Ask questions and share experiences

### Timeline

- **Immediate**: Old username/password authentication no longer works
- **Ongoing**: New API key authentication is the only supported method
- **Future**: Further improvements and new features will be added

---

### Device Setup

All appliances must be:
- Connected to your Electrolux account via the official mobile app
- Properly configured with aliases/names in the app
- Connected to the internet

## Installation

### HACS Installation (Recommended)

1. Add this repository to HACS: `https://github.com/albaintor/homeassistant_electrolux_status`
2. Search for "Electrolux" in HACS
3. Click Install
4. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/electrolux_status/` directory
2. Copy it to your Home Assistant `custom_components` folder
3. Restart Home Assistant

## Configuration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Electrolux"
4. Enter your API credentials:
   - API Key
   - Access Token
   - Refresh Token
5. The integration will automatically discover and add your appliances

## Supported Appliances

This integration works with Electrolux and Electrolux-owned brands (AEG, Frigidaire, Husqvarna) across multiple regions:

- **Europe/Middle East/Africa** (EMEA): My Electrolux Care, My AEG Care, Electrolux Kitchen, AEG Kitchen
- **Asia Pacific** (APAC): Electrolux Life
- **Latin America** (LATAM): Electrolux Home+
- **North America** (NA): Electrolux Oven, Frigidaire 2.0

### Device types that sould work (testing needed)

**Ovens**
- Electrolux SteamBake series
- AEG SteamBake and AssistedCooking series
- Real-time temperature monitoring
- Program control and status
- Safety lock validation

**Refrigerators**
- Electrolux UltimateTaste series
- Temperature monitoring
- Door status sensors

**Washing Machines**
- Electrolux UltimateCare and PerfectCare series
- AEG ÖKOKombi and AbsoluteCare series
- Cycle monitoring and control

**Dryers**
- Electrolux UltimateCare and PerfectCare series
- AEG AbsoluteCare series

**Dishwashers**
- Electrolux GlassCare and MaxiFlex series
- AEG GlassCare series

**Air Conditioners**
- Electrolux Comfort series

## Features

### Sensors
- Appliance state and status
- Temperature readings (current, target, food probe)
- Program and phase information
- Connection quality and diagnostics
- Door and safety lock status
- Water levels and tank status
- Filter life and maintenance alerts

### Controls
- Power on/off (with safety validation)
- Program selection
- Temperature settings
- Timer controls
- Light controls (ovens)
- Start/stop/reset commands

### Binary Sensors
- Door status
- Connection state
- Alert conditions

### Diagnostics
- Network interface information
- Software versions
- OTA update status
- Communication quality

## Troubleshooting

### Authentication Issues
- **403 Forbidden**: Check your API credentials from the developer portal - they may have expired. Regenerate your access token and refresh token from [Electrolux Developer Portal](https://developer.electrolux.one/dashboard)
- **Invalid Credentials**: Double-check your API key, access token, and refresh token from the developer portal

### Connection Issues
- Ensure appliances are connected to your Electrolux account
- Check internet connectivity of appliances
- Verify appliances are powered on and online

### Control Not Working
- Check if appliance has safety locks enabled (door open, child lock, etc.)
- Integration respects all appliance safety features
- Some controls may be disabled during active cycles

### Model Shows as Numbers
- The integration displays the actual product code (e.g., "944188772") used by Electrolux internally
- This is the most specific identifier available through the API
- Marketing model names (e.g., "BSE788380M") are not exposed by the API

### Debug Logging
Enable debug logging for detailed troubleshooting:
```yaml
logger:
  logs:
    custom_components.electrolux_status: debug
```

## Contributing

Contributions are welcome! This integration is actively maintained and improved.

### Development Setup
1. Fork the repository
2. Clone your fork
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Test scripts are available in the root directory for API testing

### Testing Your Appliances
Use the provided test scripts to verify API connectivity:
- `test_api_simple.py` - Basic appliance list test
- `test_appliance_details.py` - Detailed appliance information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/albaintor/homeassistant_electrolux_status/issues)
- **Discussions**: [GitHub Discussions](https://github.com/albaintor/homeassistant_electrolux_status/discussions)
- **Documentation**: [Electrolux Developer Portal](https://developer.electrolux.one/)
