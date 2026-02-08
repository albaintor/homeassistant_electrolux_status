#!/usr/bin/env python3
"""
Test script for Electrolux API - Send test commands to appliances
Usage: python script_test_commands.py
Credentials will be prompted for interactively or read from environment variables
"""

import asyncio
import json
import os
import sys

# Add the custom_components directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from custom_components.electrolux_status.util import ElectroluxApiClient


async def send_test_command(
    client: ElectroluxApiClient, appliance_id: str, command: dict
):
    """Send a test command to an appliance."""
    try:
        print(f"📤 Sending command to appliance {appliance_id}:")
        print(f"   Command: {json.dumps(command, indent=2)}")

        result = await client.execute_appliance_command(appliance_id, command)

        print("✅ Command executed successfully!")
        print("📨 API Response:")
        if result is not None:
            print(f"{json.dumps(result, indent=2)}")
        else:
            print("null")
        return True

    except Exception as e:
        print("❌ Command failed!")
        print("📨 API Response:")

        # Try to extract the raw JSON response from the error
        error_msg = str(e)
        # Look for JSON in the error message
        import re

        json_match = re.search(r"message=\"(\{.*\})\"", error_msg)
        if json_match:
            try:
                error_json = json.loads(json_match.group(1))
                print(f"{json.dumps(error_json, indent=2)}")
            except Exception:
                print(f"{json_match.group(1)}")
        else:
            # Fallback to showing the error message
            print(f"Error: {str(e)}")
        return False


async def show_appliance_state(client: ElectroluxApiClient, appliance_id: str):
    """Show current appliance state."""
    try:
        print(f"📊 Getting current state for appliance: {appliance_id}")
        state = await client.get_appliance_state(appliance_id)
        print("✅ Current state retrieved")

        # Show key state information
        reported = state.get("properties", {}).get("reported", {})
        print("\n📋 Current appliance state:")
        print(f"   Connection state: {reported.get('connectionState', 'Unknown')}")

        # Show some key reported values
        print("   Key reported values:")
        for key, value in reported.items():
            if key in [
                "applianceInfo",
                "networkInterface",
                "userSelections",
                "executionState",
            ]:
                if isinstance(value, dict):
                    print(f"     {key}: {json.dumps(value, indent=6)}")
                else:
                    print(f"     {key}: {value}")

        return state

    except Exception as e:
        print(f"❌ Error getting state: {e}")
        return None


async def main():
    """Main function."""
    if len(sys.argv) != 1:
        print("Usage: python script_test_commands.py")
        print("Credentials will be prompted for interactively")
        print("or read from environment variables")
        print()
        print("Environment variables (optional):")
        print("  ELECTROLUX_API_KEY")
        print("  ELECTROLUX_ACCESS_TOKEN")
        print("  ELECTROLUX_REFRESH_TOKEN")
        print()
        print("Example:")
        print("  python script_test_commands.py")
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

        print(
            f"\n🔧 Starting test command session for: {appliance_name} ({appliance_id})"
        )

        # Show initial state
        await show_appliance_state(client, appliance_id)

        # Command loop
        print("\n" + "=" * 60)
        print("COMMAND TESTING MODE")
        print("=" * 60)
        print("Enter JSON commands to send to the appliance.")
        print("Examples:")
        print('  {"cavityLight": true}')
        print('  {"light": "ON"}')
        print('  {"temperature": 5}')
        print('  {"userSelections": {"programUID": "123", "temperature": 4}}')
        print('  {"executionState": "START"}')
        print()
        print("Commands:")
        print("  'state' or 's' - Show current appliance state")
        print("  'quit' or 'q' - Exit the program")
        print("  'help' or 'h' - Show this help")
        print()

        command_count = 0

        while True:
            try:
                command_input = input(f"Command #{command_count + 1} > ").strip()

                if not command_input:
                    continue

                if command_input.lower() in ["quit", "q", "exit"]:
                    print("👋 Goodbye!")
                    break

                if command_input.lower() in ["help", "h"]:
                    print("\nCommands:")
                    print("  'state' or 's' - Show current appliance state")
                    print("  'quit' or 'q' - Exit the program")
                    print("  'help' or 'h' - Show this help")
                    print('  Or enter a JSON command like: {"cavityLight": true}')
                    print()
                    continue

                if command_input.lower() in ["state", "s"]:
                    await show_appliance_state(client, appliance_id)
                    continue

                # Try to parse as JSON
                try:
                    command = json.loads(command_input)
                    print(f"📝 Parsed command: {json.dumps(command, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
                    print("Please enter valid JSON or use 'help' for examples.")
                    continue

                # Send the command
                success = await send_test_command(client, appliance_id, command)
                command_count += 1

                if success:
                    print("✅ Command sent successfully!")
                else:
                    print("❌ Command failed!")

                # Small delay between commands
                await asyncio.sleep(0.5)

            except KeyboardInterrupt:
                print("\n👋 Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                import traceback

                traceback.print_exc()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
