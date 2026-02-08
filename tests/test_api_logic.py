"""Test API logic functions."""

from custom_components.electrolux_status.api import (
    ElectroluxLibraryEntity,
    deep_merge_dicts,
)
from custom_components.electrolux_status.util import string_to_boolean


class TestDeepMergeDicts:
    """Test the deep_merge_dicts function."""

    def test_deep_merge_dicts_basic(self):
        """Test basic dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": 3, "c": 4}
        assert result == expected

    def test_deep_merge_dicts_nested(self):
        """Test nested dictionary merging."""
        dict1 = {"a": {"x": 1, "y": 2}, "b": 3}
        dict2 = {"a": {"y": 4, "z": 5}, "c": 6}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": {"x": 1, "y": 4, "z": 5}, "b": 3, "c": 6}
        assert result == expected

    def test_deep_merge_dicts_deeply_nested(self):
        """Test deeply nested dictionary merging."""
        dict1 = {"a": {"b": {"c": 1, "d": 2}}}
        dict2 = {"a": {"b": {"d": 3, "e": 4}, "f": 5}}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": {"b": {"c": 1, "d": 3, "e": 4}, "f": 5}}
        assert result == expected

    def test_deep_merge_dicts_non_dict_values(self):
        """Test merging when values are not dictionaries."""
        dict1 = {"a": [1, 2], "b": "string"}
        dict2 = {"a": [3, 4], "c": {"nested": "value"}}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": [3, 4], "b": "string", "c": {"nested": "value"}}
        assert result == expected

    def test_deep_merge_dicts_empty_dicts(self):
        """Test merging with empty dictionaries."""
        dict1 = {}
        dict2 = {"a": 1}
        result = deep_merge_dicts(dict1, dict2)
        expected = {"a": 1}
        assert result == expected

    def test_deep_merge_dicts_no_modification(self):
        """Test that original dictionaries are not modified."""
        dict1 = {"a": {"x": 1}}
        dict2 = {"a": {"y": 2}}
        original_dict1 = dict1.copy()
        original_dict2 = dict2.copy()

        result = deep_merge_dicts(dict1, dict2)

        assert dict1 == original_dict1
        assert dict2 == original_dict2
        assert result == {"a": {"x": 1, "y": 2}}


class TestKeepSourceLogic:
    """Test the keep_source logic in sources_list."""

    def test_keep_source_not_blacklisted(self):
        """Test that non-blacklisted sources are kept."""
        # Create a mock ElectroluxLibraryEntity
        entity = ElectroluxLibraryEntity(
            name="test",
            status="connected",
            state={},
            appliance_info={},
            capabilities={"valid_source": {"type": "string", "access": "read"}},
        )

        # Test the keep_source function (it's a nested function, so we need to access it)
        # We'll test the logic by calling sources_list and checking the result
        result = entity.sources_list()
        assert result is not None
        assert "valid_source" in result

    def test_keep_source_blacklisted_not_whitelisted(self):
        """Test that blacklisted sources are excluded when not whitelisted."""
        entity = ElectroluxLibraryEntity(
            name="test",
            status="connected",
            state={},
            appliance_info={},
            capabilities={
                "fCMiscellaneous/blocked": {"type": "string", "access": "read"},
                "valid_source": {"type": "string", "access": "read"},
            },
        )

        result = entity.sources_list()
        assert result is not None
        assert "fCMiscellaneous/blocked" not in result
        assert "valid_source" in result

    def test_keep_source_blacklisted_but_whitelisted(self):
        """Test that blacklisted sources are included when whitelisted."""
        entity = ElectroluxLibraryEntity(
            name="test",
            status="connected",
            state={},
            appliance_info={},
            capabilities={
                "someWaterUsage": {
                    "type": "number",
                    "access": "read",
                },  # Should match .*waterUsage
                "fCMiscellaneous/blocked": {"type": "string", "access": "read"},
            },
        )

        result = entity.sources_list()
        assert result is not None
        assert "someWaterUsage" in result  # Whitelisted pattern
        assert (
            "fCMiscellaneous/blocked" not in result
        )  # Blacklisted and not whitelisted

    def test_keep_source_nested_capabilities(self):
        """Test that nested capabilities are properly handled."""
        entity = ElectroluxLibraryEntity(
            name="test",
            status="connected",
            state={},
            appliance_info={},
            capabilities={
                "parent": {
                    "child1": {"type": "string", "access": "read"},
                    "child2": {"type": "number", "access": "read"},
                },
                "fCMiscellaneous/blocked": {"type": "string", "access": "read"},
            },
        )

        result = entity.sources_list()
        assert result is not None
        assert "parent/child1" in result
        assert "parent/child2" in result
        assert "fCMiscellaneous/blocked" not in result

    def test_sources_list_with_none_capabilities(self):
        """Test sources_list when capabilities is None."""
        entity = ElectroluxLibraryEntity(
            name="test",
            status="connected",
            state={},
            appliance_info={},
            capabilities=None,
        )

        result = entity.sources_list()
        assert result is None


class TestStringToBoolean:
    """Test the string_to_boolean function."""

    def test_string_to_boolean_none_input(self):
        """Test that None input returns None."""
        result = string_to_boolean(None)
        assert result is None

    def test_string_to_boolean_true_values(self):
        """Test various string values that should return True."""
        true_values = [
            "on",
            "ON",
            "On",
            "true",
            "TRUE",
            "True",
            "yes",
            "YES",
            "Yes",
            "connected",
            "CONNECTED",
            "running",
            "RUNNING",
            "hot",
            "HOT",
            "enabled",
            "ENABLED",
            "locked",
            "LOCKED",
            "motion",
            "MOTION",
            "occupied",
            "OCCUPIED",
            "open",
            "OPEN",
            "plugged",
            "PLUGGED",
            "power",
            "POWER",
            "problem",
            "PROBLEM",
            "smoke",
            "SMOKE",
            "sound",
            "SOUND",
            "tampering",
            "TAMPERING",
            "unsafe",
            "UNSAFE",
            "update available",
            "UPDATE_AVAILABLE",
            "vibration",
            "VIBRATION",
            "wet",
            "WET",
            "charging",
            "CHARGING",
            "detected",
            "DETECTED",
            "home",
            "HOME",
            "light",
            "LIGHT",
            "locking",
            "LOCKING",
            "moving",
            "MOVING",
        ]

        for value in true_values:
            result = string_to_boolean(value)
            assert result is True, f"Expected True for '{value}', got {result}"

    def test_string_to_boolean_false_values(self):
        """Test various string values that should return False."""
        false_values = [
            "off",
            "OFF",
            "Off",
            "false",
            "FALSE",
            "False",
            "no",
            "NO",
            "No",
            "disconnected",
            "DISCONNECTED",
            "stopped",
            "STOPPED",
            "dry",
            "DRY",
            "disabled",
            "DISABLED",
            "unlocked",
            "UNLOCKED",
            "away",
            "AWAY",
            "clear",
            "CLEAR",
            "closed",
            "CLOSED",
            "normal",
            "NORMAL",
            "not charging",
            "NOT_CHARGING",
            "not occupied",
            "NOT_OCCUPIED",
            "not running",
            "NOT_RUNNING",
            "safe",
            "SAFE",
            "unlocking",
            "UNLOCKING",
            "unplugged",
            "UNPLUGGED",
            "up-to-date",
            "UP_TO_DATE",
            "no light",
            "NO_LIGHT",
            "no motion",
            "NO_MOTION",
            "no power",
            "NO_POWER",
            "no problem",
            "NO_PROBLEM",
            "no smoke",
            "NO_SMOKE",
            "no sound",
            "NO_SOUND",
            "no tampering",
            "NO_TAMPERING",
            "no vibration",
            "NO_VIBRATION",
        ]

        for value in false_values:
            result = string_to_boolean(value)
            assert result is False, f"Expected False for '{value}', got {result}"

    def test_string_to_boolean_unknown_with_fallback_true(self):
        """Test unknown values with fallback=True return the original string."""
        unknown_values = ["unknown", "maybe", "perhaps", "random_string"]

        for value in unknown_values:
            result = string_to_boolean(value, fallback=True)
            assert (
                result == value
            ), f"Expected '{value}' for unknown input, got {result}"

    def test_string_to_boolean_unknown_with_fallback_false(self):
        """Test unknown values with fallback=False return False."""
        unknown_values = ["unknown", "maybe", "perhaps", "random_string"]

        for value in unknown_values:
            result = string_to_boolean(value, fallback=False)
            assert (
                result is False
            ), f"Expected False for unknown input '{value}', got {result}"

    def test_string_to_boolean_case_insensitive(self):
        """Test that the function is case insensitive."""
        assert string_to_boolean("ON") is True
        assert string_to_boolean("on") is True
        assert string_to_boolean("On") is True
        assert string_to_boolean("OFF") is False
        assert string_to_boolean("off") is False
        assert string_to_boolean("Off") is False

    def test_string_to_boolean_underscore_handling(self):
        """Test that underscores are converted to spaces."""
        assert string_to_boolean("update_available") is True
        assert string_to_boolean("not_running") is False
        assert string_to_boolean("up_to_date") is False

    def test_string_to_boolean_whitespace_handling(self):
        """Test that extra whitespace is normalized."""
        assert string_to_boolean("  on  ") is True
        assert string_to_boolean("off\t") is False
        assert string_to_boolean(" true ") is True
