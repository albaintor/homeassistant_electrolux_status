# Air Conditioner Temperature Fix Documentation

## Problem Description
The `targetTemperatureC` parameter for Electrolux air conditioner model EXP34U339CW was using incorrect parameters intended for ovens/general appliances:
- Type: "number" (should be "temperature")
- Range: 0-300°C with step 5°C (should be 15.56-32.22°C with step 1°C)
- No default value (should be 15.56°C)

This caused temperature commands to fail for air conditioners.

## Solution Implementation

### 1. Created Air Conditioner Specific Catalog
**File:** `custom_components/electrolux_status/catalog_air_conditioner.py`

Created a dedicated catalog with correct air conditioner parameters:
- `targetTemperatureC`: type "temperature", range 15.56-32.22°C, step 1°C, default 15.56°C
- `targetTemperatureF`: type "temperature", range 60-90°F, step 1°F, default 60°F
- Additional AC-specific entities: mode, fanSpeedSetting, sleepMode, etc.

### 2. Integrated AC Catalog into Main System
**File:** `custom_components/electrolux_status/catalog_core.py`

Added:
- Import for air conditioner catalog
- Mapping for EXP34U339CW model to use AC catalog

### 3. Enhanced Appliance Type Detection
**File:** `custom_components/electrolux_status/api.py`

Enhanced the `catalog` property to:
- Check specific model first (EXP34U339CW)
- Detect appliance type and use AC catalog for any appliance with "AC" in type
- Fall back to base catalog for other appliances

## Technical Details

### Air Conditioner Temperature Parameters
According to official Electrolux API documentation:
```json
{
  "targetTemperatureC": {
    "type": "temperature",
    "min": 15.56,
    "max": 32.22, 
    "step": 1,
    "default": 15.56
  }
}
```

### Before Fix (Incorrect - for ovens)
```python
"targetTemperatureC": ElectroluxDevice(
    capability_info={
        "access": "readwrite",
        "type": "number",      # Wrong type
        "max": 300.0,          # Wrong max (oven temperature)
        "min": 0,              # Wrong min
        "step": 5.0,           # Wrong step
    },
    # ... no default value
)
```

### After Fix (Correct - for air conditioners)
```python
"targetTemperatureC": ElectroluxDevice(
    capability_info={
        "access": "readwrite",
        "type": "temperature", # Correct type
        "max": 32.22,          # Correct AC max temp
        "min": 15.56,          # Correct AC min temp  
        "step": 1,             # Correct step size
        "default": 15.56,      # Correct default
    },
    device_class=NumberDeviceClass.TEMPERATURE,
    unit=UnitOfTemperature.CELSIUS,
    entity_category=None,
    entity_icon="mdi:thermometer",
)
```

## Testing

Created verification tests:
- `test_catalog_structure.py` - Verifies file structure and parameter values
- Tests confirm correct integration of AC catalog

## Impact

This fix ensures:
1. **EXP34U339CW model** gets correct AC temperature parameters
2. **Any appliance with "AC" in type** uses AC catalog automatically  
3. **Temperature commands work properly** for air conditioners
4. **Backward compatibility** maintained for other appliance types
5. **Extensible system** for future AC models

## Files Modified

1. `catalog_air_conditioner.py` - NEW: AC-specific catalog
2. `catalog_core.py` - Added AC catalog import and model mapping
3. `api.py` - Enhanced catalog selection logic
4. `test_catalog_structure.py` - NEW: Verification test

## Usage

The fix is automatic:
- Users with EXP34U339CW will get correct AC parameters
- Temperature commands will work within proper AC range (15.56-32.22°C)
- Home Assistant UI will show appropriate temperature controls
- Commands sent to Electrolux API will be properly formatted

## Future Enhancements

This architecture allows easy addition of other AC models:
1. Add model to `CATALOG_MODEL` mapping, or
2. Ensure appliance type contains "AC" for automatic detection
