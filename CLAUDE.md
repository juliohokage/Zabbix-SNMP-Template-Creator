# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zabbix SNMP Template Generator - A Python tool that automates creation of Zabbix templates for SNMP-enabled devices. It extracts MIB data from Excel files and generates Zabbix-compatible JSON templates with SNMP items, traps, discovery rules, and item prototypes.

## Running the Project

**Main command:**
```bash
python main.py <path_to_excel_file>
```

Example:
```bash
python main.py ./sample_template_file.xlsx
```

**Installation:**
```bash
pip install -r requirements.txt
```

## Architecture

### Data Flow
1. **Excel Input** → MIBValidator extracts 4 sheets: Template Information, SNMP Items, SNMP Traps, MIB Data
2. **Validation** → Items and traps are validated against MIB data (matching by OID or Name)
3. **Object Creation** → Template class creates all Zabbix objects using ThreadPoolExecutor for parallel processing
4. **JSON Generation** → Each object generates its JSON representation
5. **Output** → Final JSON template saved to `./created_templates/` directory

### Key Components

**utils/mib_validator.py:**
- `extract_from_excel()` - Reads Excel sheets, returns preprocessed data
- `_preprocess_and_validate()` - Matches SNMP items/traps against MIB data, raises UnmatchedDataError if validation fails
- `_collect_discovery_rule_tables()` - Identifies tables in MIB data (entries with "Table" in name and "SEQUENCE OF" type), creates discovery rules from OID hierarchies

**zabbix_objects/template.py:**
- Main orchestrator that creates all Zabbix objects
- Uses ThreadPoolExecutor to create SNMPItems, SNMPTraps, and DiscoveryRules in parallel
- Adds snmp_walk_item from each discovery rule to template's items list
- Generates template description with MIB module list

**zabbix_objects/discovery_rule.py:**
- Creates SNMPWalkItem as master item
- Generates ItemPrototypes from discovery rule table (skips first entry which is the master)
- Key and name derived from master item (replacing "walk" with "discovery")

**zabbix_objects/snmp_item.py, snmp_trap.py:**
- Generate Zabbix monitoring items from validated MIB data
- Handle value type mapping (DISPLAYSTRING→CHAR, Integer32→numeric, etc.)
- Generate unique keys in format: `{template-name}.{item-name}.get` (max 255 chars)

**utils/config.py:**
- Contains SimpleNamespace objects with default values for all Zabbix object types
- Defines standard values: history retention, update intervals, value types

### Output Format
Templates are saved as: `./created_templates/YYYYMMDD_HHMMSS {Template Name} Template.json`

Format is Zabbix 7.0 JSON export format with:
- Template groups, items, discovery rules
- Item prototypes nested under discovery rules
- Tags and macros from Template Information sheet

## Excel File Structure

Required sheets:
- **Template Information**: Group, Macros, Manufacturer, Model, Tags, Device
- **SNMP Items**: OID, Name (must match MIB data)
- **SNMP Traps**: OID, Name (must match MIB data)
- **MIB Data**: MIB Module, OID, Name, Description, Type

Discovery rules are auto-generated from MIB Data where Name contains "Table" and Type is "SEQUENCE OF".

## Common Patterns

**Adding new Zabbix object types:**
1. Create class in `zabbix_objects/` with `generate_json_dict()` method
2. Add config defaults to `utils/config.py`
3. Import and instantiate in `template.py`
4. Add to JSON assembly in `main.py:create_all_json()`

**Value type determination:**
- DISPLAYSTRING/OCTET STRING → CHAR
- Integer32 → numeric (None, uses Zabbix default)
- Float → FLOAT
- Everything else → TEXT

**Key generation:**
Keys follow pattern: `{template-name}.{item-name}.{action}` with spaces→periods in template name, spaces→hyphens in item name, all lowercase.
