#!/usr/bin/env python3
"""
Test script for Electrolux API - Get appliances list
Run this script with your API credentials to test the connection.
"""

import asyncio
import os
import sys

# Add the custom_components directory to the path so we can import the util module
sys.path.insert(0, os.path.dirname(__file__))

from custom_components.electrolux_status.util import ElectroluxApiClient


async def test_appliances_list(api_key: str, access_token: str, refresh_token: str):
    """Test getting the appliances list from Electrolux API."""
    print("Testing Electrolux API connection...")
    print(f"API Key: {api_key[:10]}...")
    print(f"Access Token: {access_token[:10]}...")
    print(f"Refresh Token: {refresh_token[:10]}...")
    print()

    try:
        # Create the API client
        client = ElectroluxApiClient(api_key, access_token, refresh_token)
        print("✓ API client created successfully")

        # Get appliances list
        print("Fetching appliances list...")
        appliances = await client.get_appliances_list()
        print(f"✓ Found {len(appliances)} appliance(s)")
        print()

        # Display results
        for i, appliance in enumerate(appliances, 1):
            print(f"Appliance {i}:")
            print(f"  ID: {appliance['applianceId']}")
            print(f"  Name: {appliance['applianceName']}")
            print(f"  Type: {appliance['applianceType']}")
            print(f"  Model: {appliance['applianceData']['modelName']}")
            print(f"  Connection: {appliance['connectionState']}")
            print()

        return appliances

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


async def main():
    """Main function to run the test."""
    # Get credentials from environment variables or command line
    api_key = os.getenv("ELECTROLUX_API_KEY")
    access_token = os.getenv("ELECTROLUX_ACCESS_TOKEN")
    refresh_token = os.getenv("ELECTROLUX_REFRESH_TOKEN")

    if not api_key or not access_token or not refresh_token:
        print("Please provide your Electrolux API credentials:")
        print("Set environment variables:")
        print("  export ELECTROLUX_API_KEY='your_api_key'")
        print("  export ELECTROLUX_ACCESS_TOKEN='your_access_token'")
        print("  export ELECTROLUX_REFRESH_TOKEN='your_refresh_token'")
        print()
        print("Or edit this script to hardcode them (not recommended for security)")
        sys.exit(1)

    await test_appliances_list(api_key, access_token, refresh_token)


if __name__ == "__main__":
    asyncio.run(main())
