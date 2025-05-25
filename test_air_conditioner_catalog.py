#!/usr/bin/env python3
"""Test script for air conditioner catalog integration."""

import sys
import os

# Add the custom_components directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'electrolux_status'))

def test_catalog_integration():
    """Test that air conditioner catalog is properly integrated."""
    
    # Test import of air conditioner catalog
    try:
        from catalog_air_conditioner import CATALOG_AIR_CONDITIONER
        print("✓ Successfully imported CATALOG_AIR_CONDITIONER")
        
        # Check targetTemperatureC definition
        if 'targetTemperatureC' in CATALOG_AIR_CONDITIONER:
            target_temp = CATALOG_AIR_CONDITIONER['targetTemperatureC']
            capability_info = target_temp.capability_info
            
            print(f"✓ targetTemperatureC found in air conditioner catalog")
            print(f"  - Type: {capability_info.get('type')}")
            print(f"  - Min: {capability_info.get('min')}")
            print(f"  - Max: {capability_info.get('max')}")
            print(f"  - Step: {capability_info.get('step')}")
            print(f"  - Default: {capability_info.get('default')}")
            
            # Verify correct air conditioner parameters
            expected_params = {
                'type': 'temperature',
                'min': 15.56,
                'max': 32.22,
                'step': 1,
                'default': 15.56
            }
            
            for param, expected_value in expected_params.items():
                actual_value = capability_info.get(param)
                if actual_value == expected_value:
                    print(f"  ✓ {param}: {actual_value} (correct)")
                else:
                    print(f"  ✗ {param}: {actual_value} (expected {expected_value})")
        else:
            print("✗ targetTemperatureC not found in air conditioner catalog")
            
    except ImportError as e:
        print(f"✗ Failed to import air conditioner catalog: {e}")
        return False
        
    # Test catalog_core integration
    try:
        from catalog_core import CATALOG_MODEL
        print("✓ Successfully imported CATALOG_MODEL")
        
        if 'EXP34U339CW' in CATALOG_MODEL:
            print("✓ EXP34U339CW model found in CATALOG_MODEL")
            ac_catalog = CATALOG_MODEL['EXP34U339CW']
            if 'targetTemperatureC' in ac_catalog:
                print("✓ targetTemperatureC found in EXP34U339CW catalog")
            else:
                print("✗ targetTemperatureC not found in EXP34U339CW catalog")
        else:
            print("✗ EXP34U339CW model not found in CATALOG_MODEL")
            
    except ImportError as e:
        print(f"✗ Failed to import catalog_core: {e}")
        return False
        
    print("\n" + "="*50)
    print("SUMMARY: Air conditioner catalog integration test completed")
    print("="*50)
    
    return True

if __name__ == "__main__":
    print("Testing Air Conditioner Catalog Integration")
    print("="*50)
    test_catalog_integration()
