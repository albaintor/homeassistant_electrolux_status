#!/usr/bin/env python3
"""
Combined test script for Electrolux API - Get appliances list and appliance details
Usage: python script_appliance_details.py
Credentials will be prompted for interactively or read from environment variables
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the custom_components directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from custom_components.electrolux_status.util import ElectroluxApiClient


async def get_appliance_details(client: ElectroluxApiClient, appliance_id: str):
    """Get detailed appliance information."""
    try:
        # Get appliance state
        print(f"📊 Getting state for appliance: {appliance_id}")
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
    if len(sys.argv) != 1:
        print("Usage: python script_appliance_details.py")
        print("Credentials will be prompted for interactively")
        print("or read from environment variables")
        print()
        print("Environment variables (optional):")
        print("  ELECTROLUX_API_KEY")
        print("  ELECTROLUX_ACCESS_TOKEN")
        print("  ELECTROLUX_REFRESH_TOKEN")
        print()
        print("Example:")
        print("  python script_appliance_details.py")
        sys.exit(1)

    # Get credentials from environment variables or prompt user
    api_key = os.getenv("ELECTROLUX_API_KEY")
    access_token = os.getenv("ELECTROLUX_ACCESS_TOKEN")
    refresh_token = os.getenv("ELECTROLUX_REFRESH_TOKEN")

    if not api_key:
        api_key = input("Enter your Electrolux API Key: ").strip()
    if not access_token:
        access_token = input("Enter your Electrolux Access Token: ").strip()
    if not refresh_token:
        refresh_token = input("Enter your Electrolux Refresh Token: ").strip()

    if not api_key or not access_token or not refresh_token:
        print(
            "All credentials are required. Please provide your Electrolux API credentials."
        )
        print("You can also set environment variables:")
        print("  export ELECTROLUX_API_KEY='your_api_key'")
        print("  export ELECTROLUX_ACCESS_TOKEN='your_access_token'")
        print("  export ELECTROLUX_REFRESH_TOKEN='your_refresh_token'")
        sys.exit(1)

    try:
        client = ElectroluxApiClient(api_key, access_token, refresh_token)
        print("✅ API client initialized")

        # Get appliances list
        print("\n🔍 Fetching appliances list...")
        appliances = await client.get_appliances_list()
        print(f"✅ Found {len(appliances)} appliance(s)")

        if not appliances:
            print("No appliances found.")
            return

        # Display appliances as numbered list
        print("\n📋 Available appliances:")
        for i, appliance in enumerate(appliances, 1):
            print(f"  {i}. {appliance['applianceName']} ({appliance['applianceId']})")
            print(f"     Type: {appliance['applianceType']}")
            print(
                f"     Model: {appliance.get('applianceData', {}).get('modelName', 'Unknown')}"
            )
            print(f"     Connection: {appliance['connectionState']}")
            print()

        # Ask user to choose an appliance
        while True:
            try:
                choice = input("Choose an appliance (enter number): ").strip()
                choice_num = int(choice)
                if 1 <= choice_num <= len(appliances):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(appliances)}")
            except ValueError:
                print("Please enter a valid number")

        selected_appliance = appliances[choice_num - 1]
        appliance_id = selected_appliance["applianceId"]
        appliance_name = selected_appliance["applianceName"]

        print(f"\n🔍 Getting details for: {appliance_name} ({appliance_id})")

        # Get appliance details
        state, capabilities = await get_appliance_details(client, appliance_id)

        # Save details to file regardless of success/failure
        model_name = selected_appliance.get("applianceData", {}).get(
            "modelName", "Unknown"
        )
        # Strip PNC (appliance ID) from model name if present
        model_without_pnc = model_name.replace(appliance_id, "").strip()
        if not model_without_pnc:  # If stripping left nothing, use original
            model_without_pnc = model_name
        # Make model name safe for filename (remove/replace special characters)
        safe_model = (
            model_without_pnc.replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
        )
        filename = f"{safe_model}.txt"
        temp_filename = f"{safe_model}.tmp"
        print(f"\n💾 Saving details to {filename}...")

        try:
            print(f"Debug: Opening temp file {temp_filename} for writing...")
            with open(temp_filename, "w", encoding="utf-8") as f:
                print("Debug: Temp file opened successfully, writing header...")
                f.write("=" * 50 + "\n")
                f.write("APPLIANCE DETAILS\n")
                f.write("=" * 50 + "\n")
                f.write(f"Name: {appliance_name}\n")
                f.write(f"ID: {appliance_id}\n")
                f.write(f"Type: {selected_appliance['applianceType']}\n")
                f.write(
                    f"Model: {selected_appliance.get('applianceData', {}).get('modelName', 'Unknown')}\n"
                )
                f.write(f"Connection: {selected_appliance['connectionState']}\n")
                f.write(f"Retrieved at: {datetime.now().isoformat()}\n")
                f.write("\n")
                print("Debug: Header written, checking state data...")

                if state:
                    print("Debug: Writing state data...")
                    try:
                        f.write("RAW STATE DATA:\n")
                        f.write(json.dumps(state, indent=2))
                        f.write("\n\n")
                        print("Debug: State data written successfully")
                    except Exception as json_error:
                        print(f"Debug: Error serializing state data: {json_error}")
                        f.write("RAW STATE DATA: Error serializing data\n\n")
                else:
                    print("Debug: State data not available")
                    f.write("RAW STATE DATA: Not available\n\n")

                if capabilities:
                    print("Debug: Writing capabilities data...")
                    try:
                        f.write("RAW CAPABILITIES DATA:\n")
                        f.write(json.dumps(capabilities, indent=2))
                        f.write("\n")
                        print("Debug: Capabilities data written successfully")
                    except Exception as json_error:
                        print(
                            f"Debug: Error serializing capabilities data: {json_error}"
                        )
                        f.write("RAW CAPABILITIES DATA: Error serializing data\n")
                else:
                    print("Debug: Capabilities data not available")
                    f.write("RAW CAPABILITIES DATA: Not available\n")

                # Force disk sync before closing
                f.flush()  # Clear the internal python buffer
                os.fsync(f.fileno())  # Force the OS to write to the physical drive

            # Atomic rename to final filename
            print(f"Debug: Renaming {temp_filename} to {filename}...")
            os.rename(temp_filename, filename)
            print(f"✅ Details saved to {filename}")

        except Exception as e:
            print(f"❌ Error saving to file: {e}")
            import traceback

            traceback.print_exc()
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                    print(f"Debug: Cleaned up temp file {temp_filename}")
            except Exception:
                pass

        if state and capabilities:
            print("\n" + "=" * 50)
            print("APPLIANCE DETAILS")
            print("=" * 50)
            print(f"Name: {appliance_name}")
            print(f"ID: {appliance_id}")
            print(f"Type: {selected_appliance['applianceType']}")
            print(
                f"Model: {selected_appliance.get('applianceData', {}).get('modelName', 'Unknown')}"
            )
            print(f"Connection: {selected_appliance['connectionState']}")
            print()

            print("RAW STATE DATA:")
            print(json.dumps(state, indent=2))
            print()

            print("RAW CAPABILITIES DATA:")
            print(json.dumps(capabilities, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
