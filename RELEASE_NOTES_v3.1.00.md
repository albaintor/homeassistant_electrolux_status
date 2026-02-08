# Release Notes - v3.1.00

## 🎯 **MAJOR ENHANCEMENT: Intelligent Command Formatting & User Experience**

This release introduces **capability-driven command formatting** and **intuitive user interfaces** that automatically adapt to device capabilities, preventing API errors and providing seamless control.

### ✅ **New Features**

#### 🔧 **Capability-Driven Command System**
- **Type-Aware Value Mapping**: Commands are automatically formatted based on device capability types
- **Dynamic Command Formatting**: No more hardcoded command structures - everything adapts to device specifications
- **API Error Prevention**: Commands are validated against device capabilities before sending

#### 🎛️ **Enhanced Number Entity Controls**
- **Slider UI**: Number entities now use slider controls instead of text input for better UX
- **Automatic Step Constraints**: Sliders automatically respect device step requirements (e.g., temperature steps of 5°C)
- **Safety Rounding**: Backend validation ensures step compliance even for edge cases

#### 🛡️ **Improved Error Handling**
- **User-Friendly Error Messages**: Clear, actionable error messages instead of technical API responses
- **Type Mismatch Resolution**: Automatic handling of "Type mismatch" errors with proper value conversion
- **Command Validation**: Pre-flight validation prevents invalid commands from reaching the API

#### 🔄 **Smart Switch Controls**
- **Boolean Switches**: Proper `true`/`false` values for boolean-type switches (e.g., cavity light)
- **String/Enum Switches**: Correct string values for switches with predefined options
- **Capability-Based Formatting**: Each switch type gets the right command format automatically

### 🐛 **Bug Fixes**

All opened issues should be fixed in this version. Please check and test.

- **API Rejection Prevention**: Fixed "invalid step" and "Type mismatch" errors through capability-aware formatting
- **Command Structure Issues**: Resolved problems with nested command structures for different entity sources
- **Value Type Conversion**: Proper handling of Home Assistant boolean/string values to API-expected formats
- **SSE Event Handling**: Fixed `AttributeError: 'NoneType' object has no attribute 'update_reported_data'` crash when receiving Server-Sent Events for unknown appliances (issue #4)
- **Real-time Sensor Updates**: Fixed sensors not updating in real-time by properly handling both incremental and bulk SSE data formats from the Electrolux API (issue #3)
- **Select Entity Options**: Fixed select entities showing no options by correcting the logic that was incorrectly filtering out valid empty-dict value entries (issue #1)
- **Remote Control Status**: Fixed "Remote control disabled" errors for appliances that don't report remoteControl status by treating `None` as a valid enabled state
- **406 Error Differentiation**: Enhanced error handling for 406 responses with specific messages for type mismatches, invalid steps (with dynamic step values), and remote control status validation
- **Error Masking Fix**: Removed hardcoded 406 error handling that was masking sophisticated error analysis, allowing proper differentiation between remote control issues and other validation errors
- **Several other bug fixes I don't remember** 😊
### 🔧 **Technical Improvements**

#### **Core Architecture**
- **format_command_for_appliance()**: New utility function for dynamic command formatting
- **Capability Metadata Utilization**: Full use of device capability data for command validation
- **Type Detection**: Automatic detection of boolean, numeric, string, and enum capability types

#### **Entity Enhancements**
- **Number Entity Mode**: Configured for slider mode with automatic step constraint enforcement
- **Switch Entity Mapping**: Type-aware value mapping for all switch types
- **Error Mapping**: Enhanced error translation from API responses to user-friendly messages

#### **Safety Measures**
- **Step Rounding**: Safety mechanism to ensure numeric values meet step constraints
- **Fallback Handling**: Graceful degradation when capability data is incomplete
- **Validation Layers**: Multiple validation points to prevent API errors

### 🛠️ **Developer Tools**

#### **Testing Scripts**
- **Appliance Details Script** (`script_appliance_details.py`): Retrieves and analyzes detailed appliance information including state and capabilities
- **Command Testing Script** (`script_test_commands.py`): Interactive tool for sending test commands and monitoring API responses
- **Comprehensive Documentation**: See `TESTING_SCRIPTS_README.md` for detailed usage instructions

### 📊 **Compatibility**

- **Home Assistant**: Compatible with Home Assistant 2024.1+
- **API Compatibility**: Works with all Electrolux appliance types supported by the official SDK
- **Backward Compatibility**: All existing functionality preserved

### 🎯 **User Experience Improvements**

- **Intuitive Controls**: Sliders prevent invalid inputs naturally
- **Clear Error Messages**: Users get helpful feedback instead of technical errors
- **Automatic Adaptation**: Integration adapts to device capabilities without user configuration
- **Error Prevention**: UI constraints and backend validation prevent common API errors

### 📝 **Migration Notes**

- **No Breaking Changes**: This is a non-breaking enhancement release if updating from previous 3.x.xx versions
- **Automatic Updates**: Existing installations will benefit from improved error handling and UI
- **Entity Behavior**: Number entities will automatically switch to slider mode
- **Command Reliability**: All existing automations will work more reliably