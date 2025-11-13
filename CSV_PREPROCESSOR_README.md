# CSV Preprocessor - User Guide

## Overview

The CSV Preprocessor automates the conversion of MIB Browser CSV exports into template-ready XLSX files, eliminating 80% of manual work in the template creation process.

## Quick Start

### 1. Export MIB Data from MIB Browser

Use any MIB Browser tool (e.g., iReasoning MIB Browser) to:
1. Load your device's MIB files
2. Export to CSV format
3. Save the CSV file

### 2. Run the Preprocessor

**Interactive Mode (Recommended):**
```bash
python preprocess_csv.py your_mib_export.csv
```

**Fully Automated:**
```bash
python preprocess_csv.py your_mib_export.csv \
  --auto \
  --template-name "Cisco Router OSPF" \
  --manufacturer "Cisco" \
  --device "Router"
```

**Preview Only:**
```bash
python preprocess_csv.py your_mib_export.csv --preview-only
```

### 3. Generate Zabbix Template

```bash
python main.py generated_template.xlsx
```

## Features

### ✅ Intelligent Item Detection

The preprocessor automatically identifies and suggests:

- **Critical Items** (15+ score): `sysUpTime`, `ifOperStatus`, `sysName`, etc.
- **Important Items** (10-14 score): Status fields, utilization metrics, errors
- **Informational Items** (0-9 score): Serial numbers, descriptions, versions

### ✅ Trap Detection

Automatically detects SNMP traps based on:
- Type field: `NOTIFICATION`, `TRAP`
- Name patterns: Contains "trap", "notification"

### ✅ Smart Filtering

**Excluded from suggestions:**
- Table structures (`Table`, `Entry` definitions)
- Non-accessible objects (`not-accessible`)
- Index fields
- Structural MIB elements

**Included in suggestions:**
- Readable items (`read-only`, `read-write`, `read-create`)
- Monitoring-relevant objects
- Status and metric fields

## Usage Examples

### Example 1: Interactive Mode with Defaults

```bash
$ python preprocess_csv.py cisco_ospf_mib.csv

======================================================================
  Zabbix SNMP Template Creator - CSV Preprocessor
======================================================================

📝 TEMPLATE CONFIGURATION
----------------------------------------------------------------------
Please provide template information (press Enter for defaults):

Template Name [SNMP Template]: Cisco OSPF Router
Template Group [Templates/Network Devices]: Templates/Network Devices/Cisco
Manufacturer [Generic]: Cisco
Device Type [Network Device]: Router
Model (optional) []: ASR 1000
SNMP Macros [{$SNMP_COMMUNITY}=public]:
Tags (comma-separated) []: class:networking,protocol:ospf

🔍 ITEM SELECTION
----------------------------------------------------------------------

📊 MIB DATA ANALYSIS
======================================================================
  Total MIB Entries: 571
  Readable Items: 274
  SNMP Traps: 23
  Auto-suggested Items: 274
  Auto-suggested Traps: 23

Use auto-suggested items and traps? [Y/n]: Y
Include informational items? [Y/n]: Y

✅ Generated: cisco_ospf_router_template.xlsx
```

### Example 2: Fully Automated

```bash
python preprocess_csv.py mib_export.csv \
  --auto \
  --template-name "HP Switch" \
  --manufacturer "HP" \
  --device "Switch" \
  --model "ProCurve 2920" \
  --macros "{$SNMP_COMMUNITY}=public" \
  --tags "vendor:hp,class:networking" \
  --output hp_switch_template.xlsx
```

### Example 3: Preview Before Generation

```bash
$ python preprocess_csv.py mib_export.csv --preview-only

📊 MIB DATA ANALYSIS
======================================================================
  Total MIB Entries: 571
  Primary MIB Module: OSPFV3-MIB

  Breakdown:
    ✓ Readable Items: 274
    ✓ SNMP Traps: 23
    ✓ Tables: 58
    ✗ Not Accessible: 216

  Suggested Items by Priority:
    🔴 Critical: 56
    🟡 Important: 206
    🔵 Informational: 12

  Auto-suggested SNMP Items: 274
  Sample items (first 10):
    • entSensorStatus
    • entSensorThresholdSeverity
    • ciscoEnvMonVoltageState
    ...

✓ Preview complete. Use without --preview-only to generate XLSX file.
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `csv_file` | Path to MIB CSV export (required) | `mib_export.csv` |
| `-o, --output` | Output XLSX file path | `--output template.xlsx` |
| `--template-name` | Template name | `--template-name "Cisco Router"` |
| `--template-group` | Zabbix template group | `--template-group "Templates/Network"` |
| `--manufacturer` | Device manufacturer | `--manufacturer "Cisco"` |
| `--device` | Device type | `--device "Router"` |
| `--model` | Device model | `--model "ASR 1000"` |
| `--macros` | Template macros | `--macros "{$SNMP_COMMUNITY}=public"` |
| `--tags` | Template tags (comma-separated) | `--tags "vendor:cisco,class:network"` |
| `--auto` | Use auto-suggestions without prompts | `--auto` |
| `--no-informational` | Exclude informational items | `--no-informational` |
| `--preview-only` | Show preview without generating file | `--preview-only` |
| `--no-interactive` | Disable interactive mode | `--no-interactive --auto` |

## How Item Suggestion Works

### Importance Scoring System

```python
# Critical Items (15+ points)
- sysUpTime, sysName, sysDescr
- ifOperStatus, ifAdminStatus
- Core monitoring OIDs

# Important Items (10-14 points)
- Fields with keywords: status, state, utilization, temperature
- Error counters, fault indicators
- Capacity and threshold metrics

# Medium Priority (5-9 points)
- Regular metrics and counters
- Non-informational readable items

# Low Priority (0-4 points)
- Serial numbers, descriptions, labels
- Informational fields
```

### Filtering Logic

**Items ARE included if:**
- ✅ Access is `read-only`, `read-write`, or `read-create`
- ✅ Type is NOT `NOTIFICATION`
- ✅ Name does NOT contain `Table` or `Entry`
- ✅ Not part of structural MIB elements

**Items are EXCLUDED if:**
- ❌ Access is `not-accessible`
- ❌ It's a table/entry definition
- ❌ It's a trap/notification
- ❌ Informational (if `--no-informational` is used)

## Generated XLSX Structure

The preprocessor creates an XLSX file with 4 sheets:

### Sheet 1: Template Information
```
Group                     | Manufacturer | Device | Model | Macros                     | Tags
Templates/Network Devices | Cisco        | Router | ASR   | {$SNMP_COMMUNITY}=public  | vendor:cisco
```

### Sheet 2: SNMP Items
```
Name               | OID
sysUpTime          | .1.3.6.1.2.1.1.3.0
ifOperStatus       | .1.3.6.1.2.1.2.2.1.8
```

### Sheet 3: SNMP Traps
```
Name           | OID
linkDown       | .1.3.6.1.6.3.1.1.5.3
linkUp         | .1.3.6.1.6.3.1.1.5.4
```

### Sheet 4: MIB Data (e.g., "OSPFV3-MIB")
```
MIB Module | OID                 | Name        | Description | Type    | Syntax
SNMPv2-MIB | .1.3.6.1.2.1.1.3.0 | sysUpTime   | ...         | INTEGER |
```

## CSV Format Requirements

The preprocessor accepts CSV files with flexible column names. Common formats from MIB browsers are automatically detected and normalized.

### Minimum Required Columns
- `Name` (or `Object Name`)
- `OID` (or `Object Identifier`)
- `Type` (or `Data Type`)

### Recommended Columns
- `Access` (or `Max Access`) - For filtering readable items
- `Description` (or `Object Description`) - For documentation
- `MIB Module` (or `Module`) - For sheet naming
- `Syntax` - For enum detection (if available)

### Supported Column Mappings

The preprocessor automatically maps these common variations:
- `Object Name` → `Name`
- `Object Identifier` → `OID`
- `Data Type` → `Type`
- `Max Access` → `Access`
- `Module` → `MIB Module`
- `Object Description` → `Description`

## Troubleshooting

### Error: "CSV is missing required columns"

**Cause**: CSV doesn't have Name, OID, or Type columns

**Solution**: Check your CSV file has at least these columns. If they have different names, the preprocessor will try to map them automatically.

### Warning: "Too many informational items suggested"

**Cause**: MIB contains many serial numbers, descriptions, etc.

**Solution**: Use `--no-informational` flag to exclude these:
```bash
python preprocess_csv.py mib.csv --auto --no-informational
```

### No traps detected

**Cause**: MIB Browser export doesn't mark NOTIFICATION types, or MIB has no traps

**Solution**: This is normal for some MIBs. You can manually add traps to the SNMP Traps sheet in the generated XLSX.

### Generated template has too many items

**Cause**: Auto-suggestion includes all readable items

**Solution**:
1. Use `--preview-only` to see suggestions first
2. Manually edit the generated XLSX to remove unwanted items
3. Or use the web interface (coming soon) for interactive selection

## Best Practices

### 1. Preview First
Always use `--preview-only` to see what will be included:
```bash
python preprocess_csv.py mib.csv --preview-only
```

### 2. Start Conservative
For first-time use, exclude informational items:
```bash
python preprocess_csv.py mib.csv --auto --no-informational
```

### 3. Customize After Generation
The generated XLSX can be manually edited before running `main.py`:
- Remove unwanted items from "SNMP Items" sheet
- Add custom items not auto-detected
- Adjust template information

### 4. Save Configurations
For repeated use with similar devices, save your command:
```bash
# Create a script: generate_cisco_template.sh
python preprocess_csv.py "$1" \
  --auto \
  --template-name "Cisco Router" \
  --manufacturer "Cisco" \
  --device "Router" \
  --no-informational \
  --output "cisco_router_template.xlsx"
```

## Integration with Main Workflow

### Complete Workflow

```bash
# Step 1: Export MIB from MIB Browser to CSV
# (Manual step in MIB Browser tool)

# Step 2: Preprocess CSV to XLSX
python preprocess_csv.py mib_export.csv

# Step 3: Generate Zabbix template
python main.py generated_template.xlsx

# Step 4: Import to Zabbix
# (Manual step in Zabbix UI: Configuration → Templates → Import)
```

### Time Savings

**Before CSV Preprocessor:**
- Export MIB: 2 minutes
- **Manually create XLSX sheets: 30-60 minutes** ⏱️
- Run template generator: 1 minute
- **Total: ~35-65 minutes**

**With CSV Preprocessor:**
- Export MIB: 2 minutes
- **Run preprocessor: 30 seconds** ⚡
- Run template generator: 1 minute
- **Total: ~4 minutes** 🎉

**Time saved: 80-95%!**

## Advanced Usage

### Custom Item Selection (Coming Soon)

Future version will support JSON configuration for custom item selection:

```json
{
  "include_patterns": ["*Status", "*Utilization", "*Temperature"],
  "exclude_patterns": ["*Index", "*Entry", "*Serial*"],
  "critical_items": ["sysUpTime", "ifOperStatus"],
  "include_all_traps": true
}
```

### Batch Processing

Process multiple MIBs:
```bash
for mib in mibs/*.csv; do
  python preprocess_csv.py "$mib" --auto --output "templates/$(basename $mib .csv).xlsx"
done
```

## Web Interface Integration

The CSV preprocessor functionality is also available through the web interface (coming soon):

1. Upload CSV file
2. Review auto-suggested items
3. Customize selection interactively
4. Generate XLSX or template JSON directly

See `WEB_INTERFACE_README.md` for details.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review generated XLSX in Excel/LibreOffice to verify structure
- Open an issue on GitHub with:
  - Sample CSV file (or first 20 rows)
  - Command used
  - Error message

## Examples Directory

See `examples/` directory for sample CSV files and generated templates (coming soon).
