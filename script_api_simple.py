#!/usr/bin/env python3
"""
Simple test script for Electrolux API - Get appliances list
Usage: python test_api_simple.py "your_api_key" "your_access_token" "your_refresh_token"
"""

import asyncio
import os
import sys

# Add the custom_components directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from custom_components.electrolux_status.util import ElectroluxApiClient


async def test_api(api_key: str, access_token: str, refresh_token: str):
    """Test the Electrolux API with provided credentials."""
    print("🔍 Testing Electrolux API connection...")

    try:
        client = ElectroluxApiClient(api_key, access_token, refresh_token)
        print("✅ API client initialized")

        appliances = await client.get_appliances_list()
        print(f"✅ Found {len(appliances)} appliance(s)")

        for appliance in appliances:
            print(f"\n🏠 Appliance: {appliance['applianceName']}")
            print(f"   ID: {appliance['applianceId']}")
            print(f"   Type: {appliance['applianceType']}")
            print(f"   Model: {appliance['applianceData']['modelName']}")
            print(f"   Status: {appliance['connectionState']}")

        return appliances

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def main():
    """Main function."""
    if len(sys.argv) != 4:
        print(
            'Usage: python test_api_simple.py "api_key" "access_token" "refresh_token"'
        )
        print("\nExample:")
        print(
            'python test_api_simple.py "your-api-key" "your-access-token" "your-refresh-token"'
        )
        sys.exit(1)

    api_key = sys.argv[1]
    access_token = sys.argv[2]
    refresh_token = sys.argv[3]

    await test_api(api_key, access_token, refresh_token)


if __name__ == "__main__":
    asyncio.run(main())
