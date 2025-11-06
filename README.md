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

- [ ] Time-based anomaly detection triggers
- [ ] Graph prototypes for discovery rules
- [ ] Template dependency management
- [ ] Multi-MIB module support
- [ ] Web interface for easier configuration

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
   git clone https://github.com/Galileo-Suite/Zabbix-SNMP-Template-Creator.git
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

The input Excel file should contain the following sheets:

1. **Template Information**: Contains general information about the template.
2. **SNMP Traps**: Contains information about SNMP traps to be monitored.
3. **SNMP Items**: Contains information about SNMP items to be monitored.
4. **MIB Data**: Contains the MIB information for the device.

Each sheet should have the following columns:

- **SNMP Items** and **SNMP Traps**:

  - OID
  - Name

- **Template Information**:

  - Group
  - Macros
  - Manufacturer
  - Model
  - Tags
  - Device

- **MIB Data**:
  - MIB Module
  - OID
  - Name
  - Description
  - Type

Ensure that your Excel file follows this structure for the script to work correctly.

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
