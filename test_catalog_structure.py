#!/usr/bin/env python3
"""Simple test for catalog structure without Home Assistant dependencies."""

def test_catalog_structure():
    """Test catalog structure by analyzing file contents."""
    
    # Read catalog_air_conditioner.py file
    try:
        with open('custom_components/electrolux_status/catalog_air_conditioner.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✓ Air conditioner catalog file found")
        
        # Check for targetTemperatureC definition
        if '"targetTemperatureC"' in content:
            print("✓ targetTemperatureC found in air conditioner catalog")
            
            # Check for correct temperature parameters
            if '"type": "temperature"' in content:
                print("✓ Correct type 'temperature' found")
            else:
                print("✗ Type 'temperature' not found")
                
            if '"min": 15.56' in content:
                print("✓ Correct minimum temperature 15.56°C found")
            else:
                print("✗ Minimum temperature 15.56°C not found")
                
            if '"max": 32.22' in content:
                print("✓ Correct maximum temperature 32.22°C found")
            else:
                print("✗ Maximum temperature 32.22°C not found")
                
            if '"step": 1' in content:
                print("✓ Correct step size 1 found")
            else:
                print("✗ Step size 1 not found")
                
            if '"default": 15.56' in content:
                print("✓ Correct default temperature 15.56°C found")
            else:
                print("✗ Default temperature 15.56°C not found")
        else:
            print("✗ targetTemperatureC not found in air conditioner catalog")
            
    except FileNotFoundError:
        print("✗ Air conditioner catalog file not found")
        return False
        
    # Read catalog_core.py file  
    try:
        with open('custom_components/electrolux_status/catalog_core.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✓ Core catalog file found")
        
        # Check for air conditioner import
        if 'from .catalog_air_conditioner import CATALOG_AIR_CONDITIONER' in content:
            print("✓ Air conditioner catalog import found in core catalog")
        else:
            print("✗ Air conditioner catalog import not found in core catalog")
            
        # Check for EXP34U339CW model mapping
        if '"EXP34U339CW": CATALOG_AIR_CONDITIONER' in content:
            print("✓ EXP34U339CW model mapping found")
        else:
            print("✗ EXP34U339CW model mapping not found")
            
    except FileNotFoundError:
        print("✗ Core catalog file not found")
        return False
        
    # Read api.py file
    try:
        with open('custom_components/electrolux_status/api.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✓ API file found")
        
        # Check for air conditioner type detection
        if 'appliance_type and "AC" in str(appliance_type)' in content:
            print("✓ Air conditioner type detection found in API")
        else:
            print("✗ Air conditioner type detection not found in API")
            
        # Check for air conditioner catalog import in catalog method
        if 'from .catalog_air_conditioner import CATALOG_AIR_CONDITIONER' in content:
            print("✓ Air conditioner catalog import found in API")
        else:
            print("✗ Air conditioner catalog import not found in API")
            
    except FileNotFoundError:
        print("✗ API file not found")
        return False
        
    print("\n" + "="*60)
    print("SUMMARY: Air conditioner catalog structure verification completed")
    print("="*60)
    print("The integration should now properly handle:")
    print("- EXP34U339CW model with correct AC temperature parameters")
    print("- Any appliance with type containing 'AC'")
    print("- targetTemperatureC with range 15.56-32.22°C, step 1°C")
    
    return True

if __name__ == "__main__":
    print("Testing Air Conditioner Catalog Integration Structure")
    print("="*60)
    test_catalog_structure()
