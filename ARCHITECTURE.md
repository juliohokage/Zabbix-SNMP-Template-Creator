# Architecture Documentation

This document provides detailed technical documentation for the Zabbix SNMP Template Creator codebase.

## Table of Contents

- [System Overview](#system-overview)
- [Data Flow](#data-flow)
- [Module Reference](#module-reference)
- [Design Patterns](#design-patterns)
- [Configuration](#configuration)
- [Extension Points](#extension-points)

## System Overview

The Zabbix SNMP Template Creator is a Python application that transforms MIB data from Excel spreadsheets into production-ready Zabbix 7.0 JSON templates. The architecture follows a pipeline pattern with parallel processing for performance.

### Core Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Parallel Processing**: ThreadPoolExecutor used for concurrent object creation
3. **Conservative Triggers**: Low false-positive rate through intelligent filtering
4. **Extensibility**: Easy to add new trigger patterns, value types, or object types
5. **Testability**: 90%+ test coverage with comprehensive fixtures

### Technology Stack

- **Python 3.7+**: Core language
- **pandas**: Excel file parsing and data manipulation
- **openpyxl**: Excel file I/O (pandas dependency)
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **concurrent.futures**: Parallel processing

## Data Flow

```
Excel File (4 sheets)
    ↓
[MIBValidator] Extract & Validate
    ↓
MIB Data Dictionary
    ↓
[Template] ←──┬── [SNMPItem] + [Trigger] + [ValueMapping]
               ├── [SNMPTrap]
               └── [DiscoveryRule] → [ItemPrototype] + [TriggerPrototype]
    ↓
[main.py] Assemble JSON
    ↓
Zabbix 7.0 Template JSON File
```

### Detailed Pipeline

#### 1. Excel Extraction (`utils/mib_validator.py`)

**Input**: Excel file with 4 sheets
**Output**: Validated dictionaries and lists

```python
{
    'template_info': {...},        # Template metadata
    'snmp_items': [...],           # Items to create
    'snmp_traps': [...],           # Traps to create
    'mib_data': [...],             # Full MIB dataset
    'discovery_rules': {...}       # Table structures
}
```

**Process**:
1. Read all 4 sheets using pandas
2. Match SNMP Items/Traps against MIB Data by OID or Name
3. Raise `UnmatchedDataError` if validation fails
4. Identify discovery rule tables (Name contains "Table", Type is "SEQUENCE OF")
5. Extract Syntax field for enum parsing

#### 2. Parallel Object Creation (`zabbix_objects/template.py`)

**Uses ThreadPoolExecutor with 3 parallel tasks**:

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    items_future = executor.submit(create_items, ...)
    traps_future = executor.submit(create_traps, ...)
    discovery_future = executor.submit(create_discovery_rules, ...)
```

**For each object type**:
- SNMPItem: Creates item + optional trigger + optional value mapping
- SNMPTrap: Creates trap configuration
- DiscoveryRule: Creates rule + item prototypes + trigger prototypes + sub-rules

#### 3. Trigger Generation (`utils/trigger_detector.py`)

**Two-tier decision system**:

```
Item Data → Should Create Trigger?
    ↓ NO → Return None
    ↓ YES
Enum Data Available?
    ↓ YES → Create State Trigger (Priority 1)
    ↓ NO
Pattern Match?
    ↓ Utilization → Threshold Trigger (90%)
    ↓ Temperature → Threshold Trigger (80°C)
    ↓ Memory → Threshold Trigger (90%)
    ↓ Error → Rate Trigger
    ↓ Status → Generic Status Trigger
    ↓ NO → Return None
```

#### 4. JSON Assembly (`main.py`)

**Combines all objects into Zabbix format**:

```python
{
    "zabbix_export": {
        "version": "7.0",
        "templates": [{
            "template": "Template Name",
            "groups": [...],
            "items": [...],              # SNMPItems
            "discovery_rules": [         # Each with nested structure:
                {
                    "name": "...",
                    "item_prototypes": [...],
                    "trigger_prototypes": [...]
                }
            ],
            "triggers": [...],           # Triggers for items
            "valuemaps": [...]          # Value mappings for enums
        }]
    }
}
```

## Module Reference

### utils/mib_validator.py

**Purpose**: Excel extraction and MIB data validation

**Key Functions**:

```python
def extract_from_excel(file_path: str) -> Tuple[Dict, List, List, pd.DataFrame, Dict]:
    """
    Main entry point for extraction.

    Returns:
        - template_info: Dict with template metadata
        - validated_items: List of matched SNMP items
        - validated_traps: List of matched SNMP traps
        - mib_data: Full MIB DataFrame
        - discovery_rules: Dict of table structures
    """
```

```python
def _preprocess_and_validate(
    items_df: pd.DataFrame,
    traps_df: pd.DataFrame,
    mib_df: pd.DataFrame
) -> Tuple[List[Dict], List[Dict]]:
    """
    Matches items/traps to MIB data.

    Matching Strategy:
        1. Try exact OID match
        2. Try exact Name match
        3. Raise UnmatchedDataError if no match

    Returns:
        - validated_items: Items with full MIB data
        - validated_traps: Traps with full MIB data

    Raises:
        UnmatchedDataError: If any item/trap not found in MIB
    """
```

```python
def _collect_discovery_rule_tables(mib_df: pd.DataFrame) -> Dict:
    """
    Identifies table structures for discovery rules.

    Criteria:
        - Name contains "Table" (case-insensitive)
        - Type is "SEQUENCE OF"

    Returns:
        {
            'table_name': {
                'table_oid': '1.2.3.4',
                'entries': [list of child MIB entries],
                'syntax_data': {parsed enum data}
            }
        }
    """
```

**Error Handling**:
- `UnmatchedDataError`: Custom exception for validation failures
- Logs warnings for missing Syntax fields
- Handles missing sheets gracefully

---

### utils/syntax_parser.py

**Purpose**: Parse MIB Syntax fields to extract enum values

**Key Classes**:

```python
class SyntaxParser:
    """Parse MIB Syntax fields and extract enum values."""

    OK_KEYWORDS = ['up', 'ok', 'normal', 'active', 'on', 'enabled',
                   'true', 'running', 'operational']

    BAD_KEYWORDS = ['down', 'error', 'failed', 'inactive', 'off',
                    'disabled', 'false', 'notpresent', 'unknown',
                    'warning', 'critical', 'dormant', 'testing',
                    'lowerlayerdown']
```

**Key Methods**:

```python
@staticmethod
def parse_syntax(syntax_string: str) -> Optional[Dict[str, Any]]:
    """
    Parse Syntax field like: "INTEGER {up(1), down(2), testing(3)}"

    Returns:
        {
            'base_type': 'INTEGER',
            'enums': [
                {'value': '1', 'name': 'up'},
                {'value': '2', 'name': 'down'},
                ...
            ]
        }

    Returns None if no enums found or syntax invalid.
    """
```

```python
@staticmethod
def parse_description_enums(description: str) -> Optional[List[Dict[str, str]]]:
    """
    Fallback parser for Description field.

    Parses patterns like:
        "up(1) - powered on"
        "down(2) - powered off"

    Requires at least 2 enums to be meaningful.
    """
```

```python
@classmethod
def identify_ok_value(cls, enums: List[Dict[str, str]]) -> Optional[str]:
    """
    Identify which enum represents "OK" state.

    Strategy:
        1. Look for OK_KEYWORDS in enum names
        2. If binary (2 values), assume first is OK
        3. Exclude BAD_KEYWORDS and pick first remaining

    Returns:
        Enum value (as string) representing OK state
    """
```

```python
@classmethod
def identify_bad_values(cls, enums: List[Dict[str, str]],
                       ok_value: Optional[str] = None) -> List[str]:
    """
    Identify enum values representing problem states.

    Returns:
        List of enum values (as strings) for bad states
    """
```

---

### utils/trigger_detector.py

**Purpose**: Determine when and how to create triggers

**Key Classes**:

```python
class TriggerDetector:
    """Determine if and how to create triggers for SNMP items."""

    # Skip triggers for these field types
    INFORMATIONAL_KEYWORDS = [
        'serial', 'descr', 'description', 'name', 'label', 'text',
        'version', 'model', 'manufacturer', 'location', 'contact',
        'alias', 'ident', 'string', 'comment', 'note', 'caption',
        'address', 'mac', 'ip', 'port', 'slot', 'index', 'number',
        'uptime', 'time', 'date', 'timestamp', 'age', 'lastchange'
    ]

    UTILIZATION_KEYWORDS = ['util', 'usage', 'percent', 'cpu', 'load',
                           'busy', 'occupation']
    TEMPERATURE_KEYWORDS = ['temp', 'temperature', 'celsius',
                            'fahrenheit', 'thermal']
    ERROR_KEYWORDS = ['error', 'drop', 'discard', 'loss', 'collision',
                      'fail', 'bad', 'corrupt', 'invalid', 'overflow',
                      'underrun', 'crc', 'fcs']
    MEMORY_KEYWORDS = ['memory', 'mem', 'buffer', 'pool', 'heap', 'ram']
    STATUS_KEYWORDS = ['status', 'state', 'admin', 'oper', 'link',
                       'condition']
```

**Key Methods**:

```python
@classmethod
def should_create_trigger(cls, item_data: Dict[str, Any]) -> bool:
    """
    First-pass filter: should this item have a trigger?

    Returns False if:
        - Field name contains INFORMATIONAL_KEYWORDS
        - Type is text-only (DISPLAYSTRING, OCTET STRING)

    Conservative approach to minimize false positives.
    """
```

```python
@classmethod
def analyze_item(cls, item_data: Dict[str, Any],
                enum_data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Main analysis function. Returns trigger configuration or None.

    Priority Order:
        1. Enum-based state trigger (if enum_data provided)
        2. Utilization pattern → threshold trigger
        3. Temperature pattern → threshold trigger
        4. Error pattern → rate trigger
        5. Memory pattern → threshold trigger
        6. Status pattern → generic status trigger

    Returns:
        {
            'type': 'state' | 'threshold' | 'rate',
            'expression_template': 'last()>{$MACRO}',
            'severity': 'AVERAGE' | 'HIGH' | 'WARNING',
            'ok_value': '1',  # For state triggers
            'macro_name': '{$CPU.UTIL.MAX}',
            'macro_value': '90',
            'description_template': 'CPU utilization too high',
            'use_time_function': False
        }
    """
```

**Internal Methods**:

- `_create_state_trigger_config()`: For enum-based status fields
- `_create_utilization_trigger_config()`: For CPU/utilization metrics
- `_create_temperature_trigger_config()`: For temperature sensors
- `_create_error_rate_trigger_config()`: For error counters
- `_create_memory_trigger_config()`: For memory utilization
- `_create_generic_status_trigger_config()`: Fallback for status fields
- `_generate_macro_name()`: Creates Zabbix macro names from field names

---

### utils/index_detector.py

**Purpose**: Hybrid scoring system to identify table index fields

**Key Functions**:

```python
def detect_index_oids(discovery_table_entries: List[Dict[str, Any]],
                     max_indices: int = 3,
                     min_score: int = 10) -> List[Dict[str, Any]]:
    """
    Identify best index fields using hybrid scoring.

    Scoring System:
        Name Keywords (+30 points):
            'index': +30, 'id': +25, 'num': +20, 'number': +20,
            'descr': +15, 'name': +15, 'ident': +10

        Type Scoring (+20 points max):
            'integer32': +20, 'integer': +20, 'gauge32': +15,
            'counter32': +10, 'displaystring': +10

        Position Bias (decreases with position):
            Position 0: +15, Position 1: +12, Position 2: +9, etc.

    Args:
        discovery_table_entries: List of MIB entries in table
        max_indices: Maximum number of indices to select (default 3)
        min_score: Minimum score threshold (default 10)

    Returns:
        Sorted list of index entries (highest score first)
        Ensures at least 1 index even if scores are low
    """
```

```python
def generate_lld_macro_name(field_name: str) -> str:
    """
    Generate LLD macro name from field name.

    Process:
        1. Remove common prefixes: 'if', 'ent', 'cisco', etc.
        2. Convert to uppercase
        3. Wrap in {#...} format

    Examples:
        'ifIndex' → '{#INDEX}'
        'entPhysicalIndex' → '{#PHYSICALINDEX}'
        'sensorName' → '{#SENSORNAME}'
    """
```

```python
def create_lld_macros(index_oids: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Create LLD macro definitions for discovery rules.

    Returns:
        [
            {
                'macro': '{#INDEX}',
                'path': '$..[?(@.oid=="1.2.3.4.1")].value'
            },
            ...
        ]
    """
```

---

### zabbix_objects/template.py

**Purpose**: Main template orchestrator

**Key Class**:

```python
class Template:
    """Orchestrates creation of all Zabbix template components."""

    def __init__(self, template_info, snmp_items, snmp_traps,
                 mib_data, discovery_rules):
        self.template_name = ...
        self.groups = ...
        self.macros = ...
        self.tags = ...

        # Created in parallel:
        self.items = []
        self.discovery_rules = []
        self.triggers = []
        self.valuemaps = []
```

**Key Methods**:

```python
def _create_all_items_with_triggers(self) -> Tuple[List, List, List]:
    """
    Create all SNMP items, triggers, and value mappings.

    For each item:
        1. Create SNMPItem object
        2. Parse Syntax for enums
        3. Detect if trigger should be created
        4. Create Trigger if applicable
        5. Create ValueMapping if enums exist

    Returns:
        (items_list, triggers_list, valuemaps_list)
    """
```

```python
def _create_all_discovery_rules_parallel(self) -> List:
    """
    Create all discovery rules with sub-rules if needed.

    For each table:
        1. Calculate total OID string length
        2. If > 2048 chars, create sub-discovery rules
        3. Otherwise, create single discovery rule
        4. Add walk item to template items list

    Returns:
        List of DiscoveryRule objects
    """
```

---

### zabbix_objects/snmp_item.py

**Purpose**: SNMP item creation and configuration

**Key Class**:

```python
class SNMPItem:
    """Represents a single SNMP item in Zabbix."""

    def __init__(self, item_data: Dict, template_name: str):
        self.name = item_data['Name']
        self.oid = item_data['OID']
        self.type = self._determine_value_type(item_data['Type'])
        self.key = self._generate_unique_key()
        self.description = item_data.get('Description', '')
        # ... other fields from config.SNMP_ITEM_DEFAULTS
```

**Key Methods**:

```python
def _determine_value_type(self, mib_type: str) -> Optional[int]:
    """
    Map MIB type to Zabbix value type.

    Mapping:
        DISPLAYSTRING → 4 (TEXT/CHAR)
        OCTET STRING → 4 (TEXT/CHAR)
        Integer32 → None (numeric - uses Zabbix default)
        Float → 0 (FLOAT)
        Everything else → 1 (TEXT)
    """
```

```python
def _generate_unique_key(self) -> str:
    """
    Generate Zabbix item key.

    Format: {template-name}.{item-name}.get

    Process:
        1. Template name: spaces → periods, lowercase
        2. Item name: spaces → hyphens, lowercase
        3. Max length: 255 characters

    Example:
        Template: "Cisco Switch"
        Item: "Interface Status"
        Key: "cisco.switch.interface-status.get"
    """
```

---

### zabbix_objects/discovery_rule.py

**Purpose**: Discovery rule and item prototype creation

**Key Class**:

```python
class DiscoveryRule:
    """Represents an SNMP discovery rule with item prototypes."""

    def __init__(self, table_name: str, table_data: Dict,
                 template_name: str, is_sub_rule: bool = False,
                 parent_lld_macros: List[Dict] = None):

        # Create SNMP walk item as master
        self.snmp_walk_item = SNMPWalkItem(...)

        # Create item prototypes (skip first entry if it's the master)
        self.item_prototypes = [...]

        # Detect indices and create LLD macros
        self.lld_macros = create_lld_macros(detect_index_oids(...))

        # Create trigger prototypes
        self.trigger_prototypes = [...]
```

**Key Methods**:

```python
def _should_create_subdiscovery(self, table_data: Dict) -> bool:
    """
    Determine if table needs sub-discovery rules.

    Returns True if:
        - OID string length > 2048 characters
        - More than ~40 entries in table
    """
```

```python
def create_subdiscovery_rules(self) -> List['DiscoveryRule']:
    """
    Split large table into multiple sub-discovery rules.

    Strategy:
        1. Identify index fields
        2. Create main rule with indices + few metrics
        3. Create sub-rules using parent LLD macros
        4. Each sub-rule has ~30-40 items
    """
```

---

### zabbix_objects/trigger.py

**Purpose**: Trigger creation from configuration

**Key Class**:

```python
class Trigger:
    """Represents a Zabbix trigger."""

    def __init__(self, item_key: str, item_name: str,
                 trigger_config: Dict, template_name: str,
                 is_prototype: bool = False):

        self.expression = self._build_expression()
        self.name = self._build_name()
        self.priority = self._map_severity()
        self.manual_close = True
        # ... other fields
```

**Key Methods**:

```python
def _build_expression(self) -> str:
    """
    Build Zabbix trigger expression.

    Types:
        state: count(#3,"ne",{$MACRO})>=2
        threshold: last()>{$MACRO}
        rate: avg(5m)>{$MACRO}

    For prototypes, replaces item key with prototype key.
    """
```

```python
@classmethod
def generate_triggers(cls, items_data: List[Dict],
                     template_name: str) -> List['Trigger']:
    """
    Bulk trigger generation.

    For each item:
        1. Parse enum data if available
        2. Analyze item with TriggerDetector
        3. Create Trigger if config returned
    """
```

---

### zabbix_objects/value_mapping.py

**Purpose**: Value mapping creation from enums

**Key Class**:

```python
class ValueMapping:
    """Represents a Zabbix value mapping."""

    def __init__(self, name: str, enum_values: List[Dict[str, str]]):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.mappings = [
            {'value': enum['value'], 'newvalue': enum['name']}
            for enum in enum_values
        ]
```

**Key Methods**:

```python
@classmethod
def generate_value_mappings(cls, items_with_enums: List[Dict]) -> List['ValueMapping']:
    """
    Bulk value mapping generation.

    Creates one mapping per item with valid enum data.
    """
```

---

### utils/config.py

**Purpose**: Default configuration values

**Structure**:

```python
from types import SimpleNamespace

SNMP_ITEM_DEFAULTS = SimpleNamespace(
    type=2,  # SNMP agent
    snmp_oid="",
    value_type=None,  # Let Zabbix decide
    history="7d",
    trends="365d",
    delay="5m"
)

SNMP_TRAP_DEFAULTS = SimpleNamespace(
    type=17,  # SNMP trap
    key_prefix="snmptrap",
    value_type=1,  # Text
    history="7d"
)

DISCOVERY_RULE_DEFAULTS = SimpleNamespace(
    type=2,  # SNMP agent
    delay="1h",
    lifetime="7d"
)

TRIGGER_DEFAULTS = SimpleNamespace(
    manual_close=1,
    recovery_mode=0  # Expression
)

# Severity mappings
SEVERITY_MAP = {
    'WARNING': 2,
    'AVERAGE': 3,
    'HIGH': 4
}
```

---

### utils/logger.py

**Purpose**: Centralized logging configuration

**Setup**:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

**Usage**: Import and use throughout codebase for consistent logging.

---

### main.py

**Purpose**: Entry point and JSON assembly

**Key Functions**:

```python
def create_all_json(template: Template) -> Dict:
    """
    Assemble final Zabbix JSON structure.

    Structure:
        {
            "zabbix_export": {
                "version": "7.0",
                "templates": [{
                    "template": name,
                    "groups": [...],
                    "items": [...],
                    "discovery_rules": [
                        {
                            "name": ...,
                            "item_prototypes": [...],
                            "trigger_prototypes": [...],
                            "lld_macro_paths": [...]
                        }
                    ],
                    "triggers": [...],
                    "valuemaps": [...]
                }]
            }
        }
    """
```

```python
def main():
    """Main execution flow."""
    # 1. Parse command line arguments
    # 2. Extract from Excel
    # 3. Create Template object (triggers parallel processing)
    # 4. Assemble JSON
    # 5. Save to timestamped file
```

## Design Patterns

### 1. Pipeline Pattern

Data flows through distinct stages:
- Excel → Validation → Object Creation → JSON Assembly → File Output

Each stage transforms data and passes to next stage.

### 2. Factory Pattern

`Template` class acts as factory for creating all Zabbix objects:
- Abstracts object creation complexity
- Centralizes configuration
- Enables parallel creation

### 3. Strategy Pattern

`TriggerDetector` uses strategy pattern for trigger creation:
- Different strategies for different item types
- Priority-based strategy selection
- Easy to add new strategies

### 4. Builder Pattern

JSON assembly builds complex nested structure incrementally:
- Separates construction from representation
- Allows different JSON representations
- Enables validation at each step

## Configuration

### Default Values

All defaults defined in `utils/config.py` using `SimpleNamespace`:

```python
# Easy to modify without changing code
SNMP_ITEM_DEFAULTS.history = "14d"  # Change history retention

# Easy to add new defaults
SNMP_ITEM_DEFAULTS.new_field = "value"
```

### Extension Points

#### Adding New Trigger Patterns

1. Add keyword list to `TriggerDetector`:
```python
NEW_PATTERN_KEYWORDS = ['keyword1', 'keyword2']
```

2. Add check in `analyze_item()`:
```python
if any(kw in name for kw in cls.NEW_PATTERN_KEYWORDS):
    return cls._create_new_pattern_trigger_config(item_data)
```

3. Implement config method:
```python
@classmethod
def _create_new_pattern_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
    return {
        'type': 'threshold',
        'expression_template': 'last()>{$MACRO}',
        'severity': 'AVERAGE',
        # ... other fields
    }
```

4. Add tests in `tests/test_trigger_detector.py`

#### Adding New Value Types

1. Update mapping in `SNMPItem._determine_value_type()`:
```python
def _determine_value_type(self, mib_type: str) -> Optional[int]:
    mib_type_lower = mib_type.lower()
    if 'newtype' in mib_type_lower:
        return 5  # New Zabbix type
    # ... existing mappings
```

2. Add tests in `tests/test_snmp_item.py`

#### Adding New Zabbix Object Types

1. Create new class in `zabbix_objects/`:
```python
class NewObject:
    def __init__(self, data: Dict):
        # Initialize fields

    def generate_json_dict(self) -> Dict:
        # Return Zabbix JSON format
```

2. Add to `Template` class:
```python
def _create_new_objects(self) -> List:
    return [NewObject(data) for data in self.new_data]
```

3. Add to JSON assembly in `main.py`:
```python
"new_objects": [obj.generate_json_dict() for obj in template.new_objects]
```

4. Add comprehensive tests

## Performance Considerations

### Parallel Processing

ThreadPoolExecutor with 3 workers for:
- SNMPItem creation
- SNMPTrap creation
- DiscoveryRule creation

**Speedup**: ~2-3x for large MIBs (100+ items)

### Memory Usage

- Pandas DataFrames loaded into memory
- Typical memory: 50-100MB for large MIBs
- No streaming needed for realistic MIB sizes

### Optimization Opportunities

1. **Lazy evaluation**: Don't create objects not needed for final JSON
2. **Caching**: Cache repeated MIB lookups
3. **Batch processing**: Process multiple Excel files in one run
4. **Incremental updates**: Update existing templates instead of recreating

## Error Handling

### Exception Hierarchy

```
Exception
    └── UnmatchedDataError (custom)
            Raised when SNMP items/traps don't match MIB data
```

### Error Recovery

- **Graceful degradation**: Missing Syntax fields → use Description
- **Conservative defaults**: Unknown types → TEXT value type
- **Logging**: All decisions logged for debugging

### Validation Points

1. **Excel structure**: All required sheets present
2. **MIB matching**: Items/traps match MIB data
3. **JSON format**: Valid Zabbix 7.0 structure
4. **Field lengths**: Keys < 255 chars, OID strings < 2048 chars

## Testing Strategy

### Unit Tests (89 tests)

- **Isolated**: Each test tests one function/method
- **Fast**: All tests run in < 2 seconds
- **Comprehensive**: 90% code coverage

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_syntax_parser.py    # Syntax parsing tests
├── test_trigger_detector.py # Trigger detection tests
├── test_index_detector.py   # Index detection tests
├── test_value_mapping.py    # Value mapping tests
└── test_trigger.py          # Trigger object tests
```

### Fixtures (`conftest.py`)

Realistic sample data for:
- MIB entries (various types)
- Discovery tables (small and large)
- Template information
- Enum definitions

### Coverage Gaps

Not covered by tests:
- `main.py` (integration/E2E)
- Excel file I/O
- File system operations
- Command-line argument parsing

Could add integration tests with sample Excel files.

## Future Architecture Considerations

### Scalability

For very large deployments:
1. **Database backend**: Store MIB data in SQLite/PostgreSQL
2. **API service**: REST API for template generation
3. **Queue processing**: Async job processing for bulk operations
4. **Caching layer**: Redis for repeated MIB lookups

### Modularity

Current architecture supports:
- **Plugin system**: Load custom trigger patterns
- **Multiple exporters**: Support Zabbix 6.x, 5.x formats
- **Input adapters**: Support CSV, JSON, database sources

### Monitoring

Add instrumentation for:
- Template generation metrics
- Error rates and types
- Performance profiling
- Usage analytics
