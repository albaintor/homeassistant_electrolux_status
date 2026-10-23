# Entry and SDK lifecycle tests

Run these offline regressions with the native Home Assistant test fixtures:

```sh
python -m pip install -r requirements_test.txt
python -m pytest tests/lifecycle/ -q
```

The tests use the actual `pyelectroluxocp==0.1.3` task-registration and close implementations. Only the websocket transport and startup authentication/appliance operations are replaced at their boundaries. An HTTP test runs an actual SDK request against a local loopback server, verifies that the SDK closes its own session, then sends a request through Home Assistant's shared session to confirm it remains usable. All credentials and appliance identifiers are synthetic.

`ManagedOneAppApi` is a bounded compatibility adapter for the pinned SDK: version 0.1.3 declares a shared mutable `_running_tasks` class attribute. Isolating that registry per client prevents one account's close from cancelling another account's tasks. The registry also cancels late callback tasks before they start. This is the only SDK-private compatibility field; HTTP-session creation and closure use the vendor's public ownership contract with no borrowed Home Assistant session. Review this adapter when replacing or upgrading the SDK.

The coordinator cases cover watched and deferred work, token/websocket renewal, concurrent and repeated shutdown, declined platform unload and account isolation. Entry cases cover the stop-event signature, authentication/setup/platform failures, cancellation, temporary credential-validation clients and refused reloads.

The same suite can be run at the declared minimum with `homeassistant==2026.7.0`, `pytest-homeassistant-custom-component==0.13.344`, `pyelectroluxocp==0.1.3` and `aiofiles==25.1.0` on Python 3.14.
