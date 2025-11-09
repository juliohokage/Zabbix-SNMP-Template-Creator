# Zabbix SNMP Template Generator

A comprehensive Python tool that automates the creation of production-ready Zabbix templates for SNMP-enabled devices. This tool extracts MIB (Management Information Base) data from Excel files and generates complete Zabbix 7.0 compatible JSON templates with intelligent trigger generation, value mappings, discovery rules, and more.

## Project Goal

The main objective is to streamline the creation of Zabbix templates for SNMP monitoring by:
- **Automating template generation** from MIB data stored in structured Excel files
- **Intelligently creating triggers** based on MIB syntax parsing and pattern matching
- **Generating value mappings** for enum-based fields automatically
- **Creating discovery rules** with item prototypes from MIB table structures
- **Supporting large MIB tables** with automatic sub-discovery rule creation
- **Ensuring production quality** with comprehensive test coverage (90%+)

This automation significantly reduces the time and effort required to set up SNMP monitoring for various devices in Zabbix, transforming hours of manual work into seconds of automated processing.

## Features

### ✅ Implemented Features

- **SNMP Items**: Automatic creation from Excel sheet with OID validation
- **SNMP Traps**: Trap monitoring configuration from Excel sheet
- **Discovery Rules**: Auto-generated from MIB table structures (SEQUENCE OF types)
- **Item Prototypes**: Created automatically for each discovery rule
- **Sub-Discovery Rules**: Hybrid scoring system handles large tables exceeding SNMP OID limits
- **Intelligent Triggers**: Automatically generated based on:
  - MIB Syntax enum parsing (state-based triggers)
  - Pattern matching (CPU, memory, temperature, errors)
  - Conservative filtering to avoid false positives
- **Trigger Prototypes**: Automatic trigger creation for discovery rule items
- **Value Mappings**: Auto-generated from MIB enum definitions
- **MIB Validation**: Items and traps validated against MIB data
- **Comprehensive Testing**: 89 unit tests with 90% code coverage

### 🎯 Features on Roadmap

#### High Priority Bug Fixes & Improvements

- [ ] **Fix trigger prototypes for Integer types**: Analyze and fix issues where trigger prototypes are not being created correctly for INTEGER/Integer32 value types
- [ ] **Add tags with LLD macros to item prototypes**: Include index LLD macros (e.g., `{#IFINDEX}`, `{#IFDESCR}`) as tags on item prototypes for better visualization and filtering in Latest Data view
- [ ] **CSV to XLSX preprocessing tool**: Create a preprocessing utility that:
  - Accepts CSV exports from MIB Browser tools
  - Automatically formats and structures data into the required Excel format (Template Information, SNMP Items, SNMP Traps, MIB Data sheets)
  - Validates and saves as properly formatted XLSX file ready for template generation
  - Eliminates manual Excel file formatting steps

#### Template Enhancement Features

- [ ] **Graph prototypes for discovery rules**: Auto-generate graph prototypes for related metrics (utilization, errors, traffic)
- [ ] **Item preprocessing support**: Add preprocessing steps to items/item prototypes (multipliers, regex, JSONPath, custom scripts)
- [ ] **Unit specification**: Automatically add units to items (%, °C, bps, packets/s) based on item type and name patterns
- [ ] **Customizable thresholds via config**: YAML/JSON configuration file for threshold values instead of hardcoded constants
- [ ] **Time-based anomaly detection triggers**: Baseline-based triggers for detecting unusual patterns

#### User Experience Improvements

- [ ] **Web interface for template generation**: Browser-based UI for easier configuration and template creation
  - Drag-and-drop file upload
  - Interactive preview and editing
  - Template validation and testing
  - Download generated templates
- [ ] **Enhanced CLI options**:
  - Batch processing for multiple files
  - Verbose/debug output modes
  - Dry-run mode to preview without generating
  - Custom output directory
  - Config file support
- [ ] **Better error messages**: More detailed validation errors with line numbers, suggestions, and recovery options

#### Template Management Features

- [ ] **Template dependency management**: Handle template linking and dependencies
- [ ] **Multi-MIB module support**: Support for templates spanning multiple MIB modules
- [ ] **Template validation**: Validate generated JSON against Zabbix schema before output
- [ ] **Export format options**: Support XML (older Zabbix versions), YAML (human-readable)
- [ ] **Template versioning**: Track template changes and maintain version history

#### Advanced Features

- [ ] **Dashboard/Screen generation**: Auto-create basic dashboards with graphs and widgets
- [ ] **Host prototype support**: Support for nested discovery scenarios (e.g., chassis → modules → interfaces)
- [ ] **Documentation generation**: Auto-generate markdown documentation for templates with item descriptions, trigger logic, and usage instructions
- [ ] **Value mapping enhancements**: Improved enum detection from descriptions and better fallback mechanisms
- [ ] **Performance optimizations**: Async processing for very large MIB files (10,000+ OIDs)
- [ ] **Plugin system**: Extensible architecture for custom trigger detectors, value mappers, and validators

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Input File Specifications](#input-file-specifications)
- [How It Works](#how-it-works)
- [Output](#output)
- [Advanced Features](#advanced-features)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- A configured Excel sheet to pull data from.

* The 'MIB Data' sheet from this was produced by exporting MIB data as a CSV from the free MIB Browser application, and then adding it to the sample document.

## Installation

1. Clone this repository to your local machine:

   ```
   git clone https://github.com/juliohokage/Zabbix-SNMP-Template-Creator.git
   cd Zabbix-SNMP-Template-Creator
   ```

2. Install the required dependencies using the `requirements.txt` file:
   ```
   pip install -r requirements.txt
   ```

- If this doesn't work, try installing them individually:
  ```
  pip install {package-name}
  ```

## Quick Start

1. **Prepare your Excel file** with MIB data (see [Input File Specifications](#input-file-specifications))

2. **Run the generator**:
   ```bash
   python main.py <path_to_excel_file>
   ```

3. **Example**:
   ```bash
   python main.py ./sample_template_file.xlsx
   ```

4. **Find your template** in `./created_templates/YYYYMMDD_HHMMSS <Template Name> Template.json`

5. **Import to Zabbix** via Configuration → Templates → Import

## Input File Specifications

The input Excel file must contain **4 required sheets** with specific column structures. See `sample_template_file.xlsx` for a complete example.

### Sheet 1: Template Information

**Purpose**: Define template metadata, groups, macros, and tags.

**Required Columns**:

| Column | Description | Example |
|--------|-------------|---------|
| Group | Template group in Zabbix | `Templates/Network Devices` |
| Macros | Template macros (optional) | `{$SNMP_COMMUNITY}=public` |
| Manufacturer | Device manufacturer | `Cisco` |
| Model | Device model | `Catalyst 3750` |
| Tags | Template tags | `Application:SNMP` |
| Device | Device type/category | `Switch` |

**Example Row**:
```
Group: Templates/Network Devices/Cisco
Macros: {$SNMP_COMMUNITY}=public
Manufacturer: Cisco
Model: Catalyst 3750
Tags: Application:SNMP, Component:Network
Device: Switch
```

**Notes**:
- Only the **first data row** is used (row 2, after header)
- Multiple tags can be comma-separated
- Macros are optional but recommended

---

### Sheet 2: SNMP Items

**Purpose**: Define which SNMP OIDs to monitor as individual items.

**Required Columns**:

| Column | Description | Example |
|--------|-------------|---------|
| OID | SNMP OID to monitor | `1.3.6.1.2.1.1.3.0` |
| Name | Item name (must match MIB Data) | `sysUpTime` |

**Example Rows**:
```
OID                    | Name
1.3.6.1.2.1.1.3.0     | sysUpTime
1.3.6.1.2.1.1.5.0     | sysName
1.3.6.1.2.1.1.1.0     | sysDescr
```

**Validation Rules**:
- Each OID or Name **must exist** in the MIB Data sheet
- Matching is done by OID first, then by Name if OID doesn't match
- Unmatched items will cause `UnmatchedDataError`

**What Happens**:
- Creates SNMP item in Zabbix template
- Automatically determines value type from MIB Type
- Generates unique item key: `{template-name}.{item-name}.get`
- Creates trigger if pattern matches (CPU, memory, status, etc.)
- Creates value mapping if MIB has enum values

---

### Sheet 3: SNMP Traps

**Purpose**: Define SNMP traps to monitor.

**Required Columns**:

| Column | Description | Example |
|--------|-------------|---------|
| OID | Trap OID | `1.3.6.1.4.1.9.9.41.2.0.1` |
| Name | Trap name (must match MIB Data) | `ciscoEnvMonShutdownNotification` |

**Example Rows**:
```
OID                        | Name
1.3.6.1.4.1.9.9.41.2.0.1  | ciscoEnvMonShutdownNotification
1.3.6.1.4.1.9.9.41.2.0.2  | ciscoEnvMonVoltageNotification
```

**Validation Rules**:
- Same matching rules as SNMP Items
- Must exist in MIB Data sheet

**What Happens**:
- Creates SNMP trap item with key: `snmptrap[{trap-name}]`
- Uses TEXT value type
- 7-day history retention

---

### Sheet 4: MIB Data

**Purpose**: Complete MIB information exported from MIB browser. This is the **master data** used for validation and enrichment.

**Required Columns**:

| Column | Description | Example | Notes |
|--------|-------------|---------|-------|
| MIB Module | MIB module name | `SNMPv2-MIB` | Informational |
| OID | Full numeric OID | `1.3.6.1.2.1.2.2.1.8` | Used for matching |
| Name | MIB object name | `ifOperStatus` | Used for matching |
| Description | Object description | `The current operational state...` | Used for enum fallback |
| Type | MIB data type | `INTEGER` or `SEQUENCE OF` | **Critical for triggers** |
| Syntax | Enum definition (**optional but important**) | `INTEGER {up(1), down(2)}` | **See Syntax Format below** |

**Example Rows**:
```
MIB Module  | OID                  | Name          | Type           | Syntax                                    | Description
SNMPv2-MIB  | 1.3.6.1.2.1.2.2      | ifTable       | SEQUENCE OF    |                                           | Interface table
SNMPv2-MIB  | 1.3.6.1.2.1.2.2.1    | ifEntry       | IfEntry        |                                           | Interface entry
SNMPv2-MIB  | 1.3.6.1.2.1.2.2.1.1  | ifIndex       | INTEGER32      |                                           | Interface index
SNMPv2-MIB  | 1.3.6.1.2.1.2.2.1.2  | ifDescr       | DISPLAYSTRING  |                                           | Interface description
SNMPv2-MIB  | 1.3.6.1.2.1.2.2.1.8  | ifOperStatus  | INTEGER        | INTEGER {up(1), down(2), testing(3)}      | Operational status
```

**How to Get MIB Data**:
1. Use a MIB browser tool (e.g., [iReasoning MIB Browser](https://www.ireasoning.com/mibbrowser.shtml) - Free)
2. Load your device's MIB files
3. Export to CSV format
4. Copy/paste into Excel MIB Data sheet

**Discovery Rule Detection**:
- Rows with **"Table"** in Name AND **"SEQUENCE OF"** in Type → Creates discovery rule
- Next row (Entry) is skipped
- All child OIDs become item prototypes
- First child is used as SNMP walk master item

---

### Syntax Column Format (CRITICAL for Triggers & Value Mappings)

The **Syntax** column is optional but **highly recommended** for status/state fields. It enables automatic trigger and value mapping generation.

**Format**: `TYPE {enumName1(value1), enumName2(value2), ...}`

**Examples**:

#### Valid Syntax Formats

```
✅ INTEGER {up(1), down(2), testing(3), unknown(4), dormant(5)}
✅ INTEGER {normal(1), warning(2), critical(3)}
✅ BITS {ethernetCsmacd(6), ieee8023adLag(161)}
✅ Integer32 {enabled(1), disabled(2)}
```

#### Common Syntax Patterns

**Status/State Fields**:
```
INTEGER {up(1), down(2), testing(3), unknown(4), dormant(5), notPresent(6), lowerLayerDown(7)}
```
→ Creates trigger: `count(#3,"ne",{$INTERFACE.STATUS.OK})>=2` where OK=1

**Administrative State**:
```
INTEGER {enabled(1), disabled(2)}
```
→ Creates trigger when value != 1

**Operational Conditions**:
```
INTEGER {other(1), ok(2), degraded(3), failed(4)}
```
→ Identifies `ok(2)` as OK value, triggers on other states

**Boolean States**:
```
INTEGER {true(1), false(2)}
```
→ Assumes first value (true) is OK

#### What If Syntax Column Is Empty?

The tool has **fallback mechanisms**:

1. **Description Parsing**: Looks for enum patterns in Description column:
   ```
   Description: "up(1) - interface is operational, down(2) - interface is down"
   ```
   → Extracts enums from description

2. **Pattern Matching**: Uses field name patterns:
   - `cpuUtil`, `cpu5sec` → CPU utilization trigger (threshold: 90%)
   - `temperature`, `temp` → Temperature trigger (threshold: 80°C)
   - `memoryUtil`, `memUsed` → Memory trigger (threshold: 90%)
   - `ifInErrors`, `packetDrops` → Error rate trigger

3. **No Trigger**: If no enums and no pattern match, no trigger is created

#### Syntax Column Best Practices

✅ **DO**:
- Include Syntax for all status/state fields
- Use exact MIB format (copy from MIB browser export)
- Include all enum values, even if unused

❌ **DON'T**:
- Leave Syntax blank for important status fields
- Modify enum names (use exact MIB names)
- Mix different enum formats in same file

#### Examples by Field Type

**Interface Status**:
```
Name: ifOperStatus
Type: INTEGER
Syntax: INTEGER {up(1), down(2), testing(3), unknown(4), dormant(5), notPresent(6), lowerLayerDown(7)}
Result: State trigger + Value mapping (1→"up", 2→"down", etc.)
```

**Power Supply Status**:
```
Name: powerSupplyStatus
Type: INTEGER
Syntax: INTEGER {normal(1), warning(2), critical(3), shutdown(4), notPresent(5)}
Result: State trigger + Value mapping
```

**CPU Utilization** (no enum):
```
Name: cpuUtilization
Type: GAUGE32
Syntax: (empty)
Result: Threshold trigger at 90% (pattern-based)
```

**Serial Number** (informational):
```
Name: serialNumber
Type: DISPLAYSTRING
Syntax: (empty)
Result: No trigger (informational field)
```

---

### Complete Excel File Example

**Minimum Working Example**:

```
Sheet: Template Information
Group                        | Macros                  | Manufacturer | Model    | Tags              | Device
Templates/Network Devices    | {$SNMP_COMMUNITY}=public| Generic      | Router   | Application:SNMP  | Router

Sheet: SNMP Items
OID              | Name
1.3.6.1.2.1.1.5.0| sysName
1.3.6.1.2.1.1.1.0| sysDescr

Sheet: SNMP Traps
OID                   | Name
1.3.6.1.6.3.1.1.5.3  | linkDown

Sheet: MIB Data
MIB Module | OID              | Name      | Type           | Syntax | Description
SNMPv2-MIB | 1.3.6.1.2.1.1.5  | sysName   | DISPLAYSTRING  |        | System name
SNMPv2-MIB | 1.3.6.1.2.1.1.1  | sysDescr  | DISPLAYSTRING  |        | System description
SNMPv2-MIB | 1.3.6.1.6.3.1.1.5| linkDown  | NOTIFICATION   |        | Link down trap
```

---

### Validation and Error Messages

**Common Validation Errors**:

#### UnmatchedDataError
```
Error: The following SNMP Items were not found in MIB data:
  - OID: 1.2.3.4.5, Name: unknownItem
```

**Solution**:
- Verify OID/Name exists in MIB Data sheet
- Check for typos (case-sensitive for Names)
- Ensure MIB Data sheet is complete

#### No Discovery Rules Generated
```
Warning: No discovery rules found in MIB data
```

**Solution**:
- Add table structures to MIB Data:
  - Name containing "Table" + Type "SEQUENCE OF"
  - Example: `ifTable` with type `SEQUENCE OF`

#### Missing Syntax Field Warning
```
Warning: No Syntax field found for ifOperStatus, will try Description fallback
```

**Solution**:
- Add Syntax column to MIB Data sheet
- Populate with enum definitions from MIB
- Not critical but reduces trigger accuracy

---

### Tips for Creating Excel Files

1. **Export from MIB Browser**: Most accurate MIB data
2. **Start Small**: Begin with 5-10 items, verify, then expand
3. **Use Sample File**: Copy structure from `sample_template_file.xlsx`
4. **Validate Early**: Run tool frequently to catch errors early
5. **Check OID Format**: Must be numeric (e.g., `1.3.6.1.2.1.1.1.0`)
6. **Include Syntax**: Dramatically improves trigger quality
7. **Test Template**: Import to Zabbix and verify functionality

## Output

The script generates a Zabbix 7.0 compatible JSON file containing the complete template. The output file will be saved in the `./created_templates/` directory with a name format of:

```
YYYYMMDD_HHMMSS <Template Name> Template.json
```

### What's Included in the Generated Template

- **Template metadata**: Name, groups, macros, tags
- **SNMP items**: With proper value types and update intervals
- **SNMP traps**: Configured for trap monitoring
- **Discovery rules**: With SNMP walk items as master items
- **Item prototypes**: For each discovered table entry
- **Triggers**: Intelligently generated based on item types
- **Trigger prototypes**: For discovery rule items
- **Value mappings**: Enum-to-text conversions for status fields
- **LLD macros**: For discovery rule indexing

## How It Works

### Architecture Overview

The tool follows a pipeline architecture:

1. **Excel Extraction** (`utils/mib_validator.py`)
   - Reads 4 required sheets from Excel file
   - Validates SNMP items/traps against MIB data
   - Identifies discovery rule tables (SEQUENCE OF types)
   - Collects MIB Syntax information for enum parsing

2. **Parallel Object Creation** (`zabbix_objects/template.py`)
   - Uses ThreadPoolExecutor for concurrent processing
   - Creates SNMPItems, SNMPTraps, and DiscoveryRules in parallel
   - Generates triggers with intelligent pattern matching
   - Creates value mappings from enum definitions

3. **Trigger Generation** (`utils/trigger_detector.py`)
   - **Priority 1**: Enum-based state triggers from MIB Syntax
   - **Priority 2**: Pattern-based triggers (CPU, memory, temperature, errors)
   - **Conservative filtering**: Skips informational fields to avoid false positives
   - Generates macros for threshold values

4. **JSON Assembly** (`main.py`)
   - Combines all objects into Zabbix 7.0 JSON format
   - Generates template with proper nesting structure
   - Saves to timestamped file in `created_templates/`

### Key Components

- **MIB Validator**: Matches items/traps to MIB data by OID or Name
- **Syntax Parser**: Extracts enum values from MIB Syntax fields
- **Trigger Detector**: Determines when and how to create triggers
- **Index Detector**: Hybrid scoring system for identifying table indices
- **Discovery Rules**: Creates item prototypes with LLD macros
- **Sub-Discovery Rules**: Splits large tables that exceed SNMP OID field limits

## Advanced Features

### Intelligent Trigger Generation

The tool creates triggers automatically using a two-tier approach:

#### 1. Enum-Based State Triggers

Parses MIB Syntax fields like:
```
INTEGER {up(1), down(2), testing(3), unknown(4)}
```

- Identifies "OK" values (up, normal, active, enabled, operational)
- Identifies "BAD" values (down, error, failed, inactive, disabled)
- Generates trigger: `count(#3,"ne",{$MACRO})>=2` (state must persist)
- Creates macro: `{$INTERFACE.STATUS.OK}` = `1`

#### 2. Pattern-Based Triggers

Matches field names against patterns:

- **CPU/Utilization**: `cpuUtil`, `processorLoad` → Threshold trigger at 90%
- **Temperature**: `temperature`, `thermal` → Threshold at 80°C
- **Memory**: `memoryUtil`, `bufferPool` → Threshold at 90%
- **Error Counters**: `ifInErrors`, `packetDrops` → Rate-based triggers

**Conservative Filtering**: Automatically skips informational fields (serial numbers, descriptions, names, etc.)

### Value Mappings

Automatically creates Zabbix value mappings from enum definitions:

```
MIB Syntax: INTEGER {up(1), down(2), testing(3)}
↓
Zabbix Value Mapping:
  1 → "up"
  2 → "down"
  3 → "testing"
```

Applied to items and item prototypes for human-readable status display.

### Sub-Discovery Rules

When a table exceeds Zabbix's SNMP OID field limit (2048 chars):

1. **Hybrid Scoring System** identifies best index fields:
   - Name matching: `index`, `id`, `num`, `descr`
   - Type scoring: INTEGER32 (high), DISPLAYSTRING (medium)
   - Position bias: Earlier fields scored higher
   - Maximum 3 indices per table

2. **Split Strategy**:
   - Creates main discovery rule with fewer items
   - Creates sub-discovery rules using LLD macros from parent
   - Maintains proper hierarchy and dependencies

### MIB Syntax Parsing

The tool parses MIB Syntax fields to extract enum values:

- **Syntax Field**: `INTEGER {up(1), down(2)}`
- **Description Fallback**: Parses enums from description if Syntax missing
- **Smart Detection**: Identifies OK/BAD states using keyword matching
- **Resilient**: Handles various MIB formats and malformed data

## Testing

The project includes comprehensive unit tests with 90% code coverage.

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_syntax_parser.py -v

# Run specific test
pytest tests/test_trigger_detector.py::TestPatternMatching::test_cpu_pattern_matching -v
```

### Test Coverage

- **89 total tests** covering:
  - MIB syntax parsing (50+ tests)
  - Trigger detection and pattern matching (30+ tests)
  - Index detection with hybrid scoring (24 tests)
  - Value mapping generation (8 tests)
  - Trigger object creation (6 tests)

- **Coverage by module**:
  - `utils/config.py`: 100%
  - `utils/logger.py`: 100%
  - `zabbix_objects/value_mapping.py`: 100%
  - `utils/index_detector.py`: 97%
  - `utils/syntax_parser.py`: 93%
  - `utils/trigger_detector.py`: 93%
  - `zabbix_objects/trigger.py`: 93%

## Troubleshooting

### Common Issues

#### UnmatchedDataError: Items/Traps not found in MIB data

**Cause**: SNMP Items or Traps sheet contains OIDs/Names that don't exist in MIB Data sheet

**Solution**:
- Verify OIDs and Names in SNMP Items/Traps match exactly with MIB Data
- Check for typos or case sensitivity issues
- Ensure MIB Data sheet is complete

#### No Discovery Rules Generated

**Cause**: MIB Data doesn't contain table structures

**Solution**:
- Discovery rules require entries with "Table" in Name and "SEQUENCE OF" in Type
- Verify MIB Data includes table definitions
- Check sample_template_file.xlsx for proper format

#### Triggers Not Being Created

**Expected Behavior**: The tool is conservative to avoid false positives

**Triggers ARE created for**:
- Status/state fields with enum values
- CPU, memory, temperature metrics
- Error counters

**Triggers are NOT created for**:
- Informational fields (serial numbers, descriptions, names)
- Text-only fields (DISPLAYSTRING)
- Fields containing keywords: `serial`, `descr`, `name`, `label`, `version`, `uptime`, `port`, `index`

#### Large Tables Cause Issues

**Automatic Handling**: Sub-discovery rules are created automatically when table OIDs exceed 2048 characters

**If issues persist**:
- Check logs for index detection warnings
- Verify table has identifiable index fields
- Review hybrid scoring system output

### Getting Help

If problems persist:

1. Check your Python version: `python --version` (requires 3.7+)
2. Verify all dependencies: `pip install -r requirements.txt`
3. Run tests to verify installation: `pytest tests/ -v`
4. Check the logs for detailed error messages
5. Open an issue on GitHub with:
   - Error message and stack trace
   - Sample Excel file (if possible)
   - Steps to reproduce
   - Python version and OS

## Contributing

Contributions are welcome! This project follows standard GitHub workflow:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Run tests**: `pytest tests/ -v --cov=.`
5. **Ensure tests pass** and coverage remains high (>85%)
6. **Commit your changes**: `git commit -m "Add feature: description"`
7. **Push to your fork**: `git push origin feature/your-feature-name`
8. **Create a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Zabbix-SNMP-Template-Creator.git
cd Zabbix-SNMP-Template-Creator

# Install dependencies including test tools
pip install -r requirements.txt

# Run tests to verify setup
pytest tests/ -v
```

### Code Standards

- **Python 3.7+** compatibility required
- **Type hints** encouraged for new functions
- **Docstrings** required for public methods
- **Test coverage**: New features must include unit tests
- **Conservative triggers**: Maintain low false-positive rate for trigger generation

### Areas for Contribution

See the [Features on Roadmap](#features) section for planned features. Other ideas:

- Additional trigger patterns for specialized equipment
- Support for more MIB export formats
- Performance optimizations for very large MIB files
- Web interface for configuration
- Template validation and testing utilities

### Documentation

When contributing, please update relevant documentation:
- Update README.md for user-facing changes
- Update CLAUDE.md for architecture changes
- Add docstrings to new functions
- Include examples in docstrings for complex functions

## License

[MIT License](LICENSE)

## Acknowledgments

- Built for Zabbix 7.0 template format
- Inspired by the need to automate SNMP template creation
- Community contributions welcome!
