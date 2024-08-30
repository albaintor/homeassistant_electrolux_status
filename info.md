# Home Assistant Electrolux Status (formerly Home Assistant Electrolux Care Integration V2)

[![Validate with HACS](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hacs.yml/badge.svg)](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hacs.yml)
[![Validate with hassfest](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hassfest.yml/badge.svg)](https://github.com/albaintor/homeassistant_electrolux_status/actions/workflows/hassfest.yml)

## Information
This is an integration to Home Assistant to communicate with the Electrolux Devices via One Connect Platform. It works with Electrolux and Electrolux owned brands, like AEG, Frigidaire, Husqvarna.
***Disclaimer*** *This Home Assistant integration was not made by Electrolux. It is not official, not developed, and not supported by Electrolux.*

## Contributing
If you are interested in contributing to the project and assisting with the integration of the new APIs, your contributions are more than welcome! Feel free to fork the repository, make changes, and submit a pull request.

Thank you for your understanding and support.

| Major Contributors | Support Link |
|-------------|--------------|
| albaintor   | [!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/albaintor) |
| kingy444    | [!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/kingy444) |

## Prerequisites
All devices need configured and Alias set in the Electrolux app prior to configuration.
If this does not occur the home assistant integration may raise an authentication error depending on device type and region such as:
- My Electrolux Care/My AEG Care (EMEA region)
- Electrolux Kitchen/AEG Kitchen (EMEA region)
- Electrolux Life (APAC region)
- Electrolux Home+ (LATAM region)
- Electrolux Oven/Frigidaire 2.0 (NA region)

## Installation
*If the integration does not appear add a new repository in HACS manually: `https://github.com/albaintor/homeassistant_electrolux_status`*
1. Search for `Electrolux Status` in HACS. 
2. Click install.
3. In the HA UI go to `Configuration` -> `Integrations` and search for `Electrolux Status`.
4. Insert your Electrolux credentials

**Known issues :**
- This integration is based on new APIs and may be unstable 
- Some commands don't work (to be investigated) : several dropdown lists like setting analog temperature...
- Upstream API does not currently support `language`

### Supported and tested devices

This list is non-exhaustive and your appliance may work even if not present here

**Fridge**

| Manufacturer | Model | Description |
| :----------- | :---- | :---------- |
| ELECTROLUX | EHE6899SA | 609L UltimateTaste 900 |
| ELECTROLUX | EHE6799SA | 609L UltimateTaste 900 |

**Dishwasher**

| Manufacturer | Model | Description |
| :----------- | :---- | :---------- |
| ELECTROLUX | EEM69410W | MaxiFlex 700|
| ELECTROLUX | EEM69410W | GlassCare 700 |
| ELECTROLUX | KEGB9300W | GlassCare 700 |
| ELECTROLUX | EEG69410W | GlassCare 700 |
| AEG | FSE76738P | 7000 GlassCare |

**Dryer**

| Manufacturer | Model | Description |
| :----------- | :---- | :---------- |
| ELECTROLUX | EDH803BEWA | UltimateCare 800 |
| ELECTROLUX | EW9H283BY | PerfectCare 900 |
| ELECTROLUX | EW9H869E9 | PerfectCare 900 |
| ELECTROLUX | EW9H869E9 | PerfectCare 900 |
| ELECTROLUX | EW9H188SPC | PerfectCare 900 |
| ELECTROLUX | YH7W979P9 | Airdryer |

**Washing Machine**

| Manufacturer | Model | Description |
| :----------- | :---- | :---------- |
| ELECTROLUX | EWF1041ZDWA | UltimateCare 900 AutoDose |
| ELECTROLUX | EW8F8669Q8 | PerfectCare 800 |
| ELECTROLUX | EW9F149SP | PerfectCare 900 |
| AEG | L6FBG841CA | 6000 Series Autodose |
| AEG | L7FENQ96 | 7000 Series ProSteam Autodose |
| AEG | L7FBE941Q | 7000 Series Prosense Autodose |
| AEG | L8FEC96QS | 8000 Series Ökomix Autodose |
| AEG | L9WBA61BC | 9000 Series ÖKOKombi DualSense SensiDry |

**Washer / Dryer Combo**

| Manufacturer | Model | Description |
| :----------- | :---- | :---------- |
| ELECTROLUX | EW9W161BC | PerfectCare 900 Washer & Dryer |

**Oven**

| Manufacturer | Model | Description |
| :----------- | :---- | :---------- |
| ELECTROLUX | EOD6P77WZ | SteamBake 600 |
| ELECTROLUX | KODDP77WX | SteamBake 600 |
| AEG | BPE558370M | SteamBake 6000 |
