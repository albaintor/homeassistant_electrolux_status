"""Dump the raw Electrolux API payloads for every appliance on an account.

Useful when adding support for a new appliance: the capability document it
prints is the source of truth the integration builds entities from.

    ELECTROLUX_USERNAME=you@example.com \
    ELECTROLUX_PASSWORD=secret \
    ELECTROLUX_COUNTRY=se \
    python testAppliance.py [output_directory]

With an output directory, one JSON file per appliance is written there instead
of everything going to stdout. Payloads contain the appliance id, PNC and
serial number, so sanitize them before attaching them to an issue or a PR.
"""

import asyncio
import json
import os
import sys

from pyelectroluxocp import OneAppApi


async def main() -> None:
    """Fetch and dump list, info, state and capabilities per appliance."""
    username = os.environ.get("ELECTROLUX_USERNAME")
    password = os.environ.get("ELECTROLUX_PASSWORD")
    country = os.environ.get("ELECTROLUX_COUNTRY", "us")
    if not username or not password:
        sys.exit("Set ELECTROLUX_USERNAME and ELECTROLUX_PASSWORD")

    output_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    async with OneAppApi(username, password, country) as client:
        appliances = await client.get_appliances_list()
        print(f"Found {len(appliances)} appliance(s)", file=sys.stderr)

        for appliance in appliances:
            appliance_id = appliance.get("applianceId")
            model_name = (appliance.get("applianceData") or {}).get("modelName", "unknown")
            print(f"== {model_name} {appliance_id}", file=sys.stderr)

            async def dump(name, coro):
                """Await one call, recording the error instead of raising."""
                try:
                    return await coro
                except Exception as err:  # noqa: BLE001
                    # Some appliances (robot vacuums for instance) have no
                    # capability document; keep going so the rest is usable.
                    detail = f"{type(err).__name__}: {err}"
                    print(f"   {name}: {detail}", file=sys.stderr)
                    return {"error": detail}

            bundle = {
                "get_appliances_list": appliance,
                "get_appliances_info": await dump(
                    "get_appliances_info", client.get_appliances_info([appliance_id])
                ),
                "get_appliance_state": await dump(
                    "get_appliance_state", client.get_appliance_state(appliance_id)
                ),
                "get_appliance_capabilities": await dump(
                    "get_appliance_capabilities", client.get_appliance_capabilities(appliance_id)
                ),
            }

            if output_dir:
                # modelName carries the appliance *type* (HB, WM, CR), so it
                # is not unique on an account with two appliances of a kind.
                # The appliance id is.
                safe_name = "".join(c if c.isalnum() else "_" for c in f"{model_name}_{appliance_id}")
                path = os.path.join(output_dir, f"{safe_name}.json")
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(bundle, handle, indent=2, sort_keys=True)
                print(f"   written to {path}", file=sys.stderr)
            else:
                print(json.dumps(bundle, indent=2, sort_keys=True))


asyncio.run(main())
