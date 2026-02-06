#!/usr/bin/env python3
"""
Test script for Electrolux API - Get appliance state and capabilities
Usage: python test_appliance_details.py "your_api_key" "your_access_token" "your_refresh_token" "appliance_id"
"""

import asyncio
import json
import os
import sys

# Add the custom_components directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from custom_components.electrolux_status.util import ElectroluxApiClient


async def test_appliance_details(
    api_key: str, access_token: str, refresh_token: str, appliance_id: str
):
    """Test getting detailed appliance information."""
    print("🔍 Testing Electrolux API - Appliance Details...")

    try:
        client = ElectroluxApiClient(api_key, access_token, refresh_token)
        print("✅ API client initialized")

        # Get appliance state
        print(f"\n📊 Getting state for appliance: {appliance_id}")
        state = await client.get_appliance_state(appliance_id)
        print("✅ Appliance state retrieved")

        # Look for model information in state
        print("\n🔍 Checking for model information in state...")
        reported = state.get("properties", {}).get("reported", {})

        # Check applianceInfo
        appliance_info = reported.get("applianceInfo", {})
        print(f"applianceInfo: {json.dumps(appliance_info, indent=2)}")

        # Check networkInterface for model info
        network_interface = reported.get("networkInterface", {})
        print(f"networkInterface: {json.dumps(network_interface, indent=2)}")

        # Look for any field containing model-like information
        print("\n🔍 Searching for model-related fields...")
        for key, value in reported.items():
            if isinstance(value, str) and (
                "model" in key.lower() or "BSE" in str(value)
            ):
                print(f"Found potential model field: {key} = {value}")

        # Get capabilities
        print(f"\n⚙️ Getting capabilities for appliance: {appliance_id}")
        capabilities = await client.get_appliance_capabilities(appliance_id)
        print("✅ Capabilities retrieved")

        # Look for model in capabilities
        print("\n🔍 Checking capabilities for model information...")
        if "keyModel" in capabilities:
            print(f"keyModel: {capabilities['keyModel']}")

        # Look for any model-related constants
        for key, value in capabilities.items():
            if isinstance(value, dict) and value.get("access") == "constant":
                if "model" in key.lower() or (
                    isinstance(value.get("default"), str) and "BSE" in value["default"]
                ):
                    print(f"Constant field: {key} = {value}")

        return state, capabilities

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return None, None


async def main():
    """Main function."""
    if len(sys.argv) != 5:
        print(
            'Usage: python test_appliance_details.py "api_key" "access_token" "refresh_token" "appliance_id"'
        )
        print("\nExample:")
        print(
            'python test_appliance_details.py "your-api-key" "your-access-token" "your-refresh-token" "944188772_00:31862190-443E07363DAB"'
        )
        sys.exit(1)

    api_key = sys.argv[1]
    access_token = sys.argv[2]
    refresh_token = sys.argv[3]
    appliance_id = sys.argv[4]

    await test_appliance_details(api_key, access_token, refresh_token, appliance_id)


if __name__ == "__main__":
    asyncio.run(main())
