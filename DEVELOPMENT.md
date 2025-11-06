# Development Guide

This guide helps developers contribute to the Zabbix SNMP Template Creator project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing Guidelines](#testing-guidelines)
- [Common Development Tasks](#common-development-tasks)
- [Debugging Tips](#debugging-tips)
- [Pull Request Process](#pull-request-process)

## Getting Started

### Prerequisites

- Python 3.7 or higher
- git
- A GitHub account
- Familiarity with SNMP and MIB concepts
- Basic understanding of Zabbix templates

### Initial Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Zabbix-SNMP-Template-Creator.git
   cd Zabbix-SNMP-Template-Creator
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/Galileo-Suite/Zabbix-SNMP-Template-Creator.git
   ```

4. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Verify installation**:
   ```bash
   pytest tests/ -v
   python main.py sample_template_file.xlsx
   ```

### Project Structure

```
Zabbix-SNMP-Template-Creator/
├── main.py                    # Entry point
├── utils/                     # Utility modules
│   ├── mib_validator.py      # Excel extraction and validation
│   ├── syntax_parser.py      # MIB Syntax parsing
│   ├── trigger_detector.py   # Trigger pattern matching
│   ├── index_detector.py     # Index field detection
│   ├── config.py             # Default configurations
│   └── logger.py             # Logging setup
├── zabbix_objects/           # Zabbix object classes
│   ├── template.py           # Template orchestrator
│   ├── snmp_item.py          # SNMP item creation
│   ├── snmp_trap.py          # SNMP trap creation
│   ├── snmp_walk_item.py     # SNMP walk items
│   ├── discovery_rule.py     # Discovery rules
│   ├── item_prototype.py     # Item prototypes
│   ├── trigger.py            # Trigger creation
│   └── value_mapping.py      # Value mappings
├── tests/                    # Unit tests
│   ├── conftest.py           # Shared fixtures
│   ├── test_syntax_parser.py
│   ├── test_trigger_detector.py
│   ├── test_index_detector.py
│   ├── test_value_mapping.py
│   └── test_trigger.py
├── created_templates/        # Generated templates
├── sample_template_file.xlsx # Example input
├── requirements.txt          # Python dependencies
├── pytest.ini               # Test configuration
├── README.md                # User documentation
├── ARCHITECTURE.md          # Technical documentation
├── DEVELOPMENT.md           # This file
└── CLAUDE.md                # AI assistant guide
```

## Development Workflow

### Branch Strategy

1. **Keep main branch clean**: Never commit directly to main
2. **Feature branches**: Create for each feature/fix
3. **Branch naming**:
   - Features: `feature/descriptive-name`
   - Bugs: `fix/issue-description`
   - Docs: `docs/what-changed`

### Typical Workflow

```bash
# Update your fork
git checkout main
git pull upstream main
git push origin main

# Create feature branch
git checkout -b feature/my-new-feature

# Make changes and commit
git add .
git commit -m "Add feature: description of changes"

# Run tests
pytest tests/ -v --cov=.

# Push to your fork
git push origin feature/my-new-feature

# Create Pull Request on GitHub
```

### Commit Messages

Follow conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples**:
```
feat(triggers): Add support for bandwidth utilization triggers

Adds pattern matching for bandwidth metrics with configurable
thresholds. Includes unit tests and documentation updates.

Closes #123
```

```
fix(syntax-parser): Handle enums with special characters

The regex pattern now correctly handles enum names containing
hyphens and underscores.
```

## Code Style

### Python Style

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters (soft limit), 120 (hard limit)
- **Indentation**: 4 spaces
- **Imports**: Group by stdlib, third-party, local
- **Docstrings**: Google style for all public functions/classes
- **Type hints**: Encouraged but not required

### Naming Conventions

```python
# Classes: PascalCase
class TriggerDetector:
    pass

# Functions/methods: snake_case
def create_all_items():
    pass

# Constants: UPPER_SNAKE_CASE
INFORMATIONAL_KEYWORDS = [...]

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

### Docstring Example

```python
def detect_index_oids(discovery_table_entries: List[Dict[str, Any]],
                     max_indices: int = 3,
                     min_score: int = 10) -> List[Dict[str, Any]]:
    """
    Identify best index fields using hybrid scoring.

    Uses a multi-factor scoring system combining name keywords,
    data types, and position to identify the most likely index
    fields in a discovery table.

    Args:
        discovery_table_entries: List of MIB entries in the table.
            Each entry should have 'Name', 'Type', and 'OID' keys.
        max_indices: Maximum number of indices to select. Default 3.
        min_score: Minimum score threshold for selection. Default 10.

    Returns:
        Sorted list of index entries (highest score first).
        Guarantees at least 1 index even if all scores < min_score.

    Example:
        >>> table_entries = [
        ...     {'Name': 'ifIndex', 'Type': 'Integer32', 'OID': '1.2.3.1'},
        ...     {'Name': 'ifDescr', 'Type': 'DisplayString', 'OID': '1.2.3.2'},
        ...     {'Name': 'ifSpeed', 'Type': 'Gauge32', 'OID': '1.2.3.3'}
        ... ]
        >>> indices = detect_index_oids(table_entries, max_indices=2)
        >>> [idx['Name'] for idx in indices]
        ['ifIndex', 'ifDescr']
    """
    # Implementation...
```

### Import Organization

```python
# Standard library imports
import re
import uuid
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

# Third-party imports
import pandas as pd

# Local imports
from utils.logger import logger
from utils.config import SNMP_ITEM_DEFAULTS
```

## Testing Guidelines

### Writing Tests

1. **Use pytest fixtures** from `conftest.py` for sample data
2. **One test per behavior**, not one test per function
3. **Descriptive test names**: `test_parse_syntax_with_missing_braces`
4. **AAA pattern**: Arrange, Act, Assert

### Test Structure

```python
class TestFeatureName:
    """Tests for FeatureName functionality."""

    def test_specific_behavior(self, fixture_name):
        """Test that specific behavior works correctly."""
        # Arrange: Set up test data
        input_data = {'key': 'value'}

        # Act: Execute the function
        result = function_under_test(input_data)

        # Assert: Verify the result
        assert result['expected_key'] == 'expected_value'
        assert len(result) == 1
```

### Coverage Requirements

- **New features**: Must include tests
- **Minimum coverage**: 85% for new code
- **Target coverage**: 90%+ overall
- **Run before committing**:
  ```bash
  pytest tests/ -v --cov=. --cov-report=term-missing
  ```

### Test Examples

```python
# Good: Tests one specific behavior
def test_identify_ok_value_with_up_keyword(self):
    """Test that 'up' keyword is identified as OK state."""
    enums = [
        {'value': '1', 'name': 'up'},
        {'value': '2', 'name': 'down'}
    ]
    result = SyntaxParser.identify_ok_value(enums)
    assert result == '1'

# Good: Tests edge case
def test_identify_ok_value_with_empty_list(self):
    """Test handling of empty enum list."""
    result = SyntaxParser.identify_ok_value([])
    assert result is None

# Good: Tests error condition
def test_parse_syntax_malformed(self):
    """Test parsing malformed syntax string."""
    syntax = "INTEGER {up(1, down(2)}"  # Missing closing paren
    result = SyntaxParser.parse_syntax(syntax)
    # Parser is resilient - extracts what it can
    assert result is not None
    assert len(result['enums']) >= 1
```

### Running Specific Tests

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_syntax_parser.py -v

# Specific class
pytest tests/test_syntax_parser.py::TestParseSyntax -v

# Specific test
pytest tests/test_syntax_parser.py::TestParseSyntax::test_parse_valid_syntax -v

# With coverage
pytest tests/ -v --cov=utils --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/ -- -v
```

## Common Development Tasks

### Adding a New Trigger Pattern

**Example**: Add support for bandwidth utilization triggers

1. **Update keyword list** (`utils/trigger_detector.py`):
   ```python
   BANDWIDTH_KEYWORDS = ['bandwidth', 'bps', 'throughput', 'bitrate']
   ```

2. **Add pattern check** in `analyze_item()`:
   ```python
   if any(keyword in name for keyword in cls.BANDWIDTH_KEYWORDS):
       return cls._create_bandwidth_trigger_config(item_data)
   ```

3. **Implement config method**:
   ```python
   @classmethod
   def _create_bandwidth_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
       """Create trigger config for bandwidth metrics."""
       macro_name = cls._generate_macro_name(
           item_data.get('Name', 'Unknown'),
           'BANDWIDTH.MAX'
       )

       return {
           'type': 'threshold',
           'expression_template': 'last()>{$MACRO}',
           'severity': 'WARNING',
           'macro_name': macro_name,
           'macro_value': '1000000000',  # 1 Gbps default
           'description_template': f"{item_data.get('Name')} exceeds threshold",
           'use_time_function': False
       }
   ```

4. **Add tests** (`tests/test_trigger_detector.py`):
   ```python
   def test_bandwidth_pattern_matching(self):
       """Test bandwidth-related field names."""
       bw_names = ['ifBandwidth', 'linkSpeed', 'throughputBps']

       for name in bw_names:
           item_data = {'Name': name, 'Type': 'GAUGE32', 'Description': 'Bandwidth'}
           result = TriggerDetector.analyze_item(item_data)
           assert result is not None, f"Failed to match: {name}"
           assert result['type'] == 'threshold'
           assert result['severity'] == 'WARNING'
   ```

5. **Run tests**:
   ```bash
   pytest tests/test_trigger_detector.py::test_bandwidth_pattern_matching -v
   ```

6. **Update documentation** in README.md

### Adding a New Value Type Mapping

**Example**: Map BITS type to TEXT in Zabbix

1. **Update mapping** (`zabbix_objects/snmp_item.py`):
   ```python
   def _determine_value_type(self, mib_type: str) -> Optional[int]:
       """Map MIB type to Zabbix value type."""
       mib_type_lower = mib_type.lower()

       # New mapping
       if 'bits' in mib_type_lower:
           return 1  # TEXT

       # Existing mappings...
   ```

2. **Add test**:
   ```python
   def test_bits_type_mapping(self):
       """Test that BITS type maps to TEXT."""
       item_data = {
           'Name': 'statusBits',
           'OID': '1.2.3.4',
           'Type': 'BITS'
       }
       item = SNMPItem(item_data, 'Test Template')
       assert item.type == 1  # TEXT
   ```

### Debugging Template Generation

**Enable debug logging**:

```python
# In utils/logger.py (temporarily)
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Or set at runtime**:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

**Check generated JSON**:

```bash
# Pretty-print generated template
python -m json.tool created_templates/20241106_*.json

# Search for specific items
cat created_templates/20241106_*.json | jq '.zabbix_export.templates[0].items[] | select(.name | contains("CPU"))'

# Count triggers
cat created_templates/20241106_*.json | jq '.zabbix_export.templates[0].triggers | length'
```

### Testing with Different MIB Files

1. **Create test Excel file** in `tests/fixtures/`:
   ```
   tests/fixtures/test_device_mib.xlsx
   ```

2. **Add test**:
   ```python
   def test_full_template_generation():
       """Integration test with real MIB file."""
       from main import main
       import sys

       # Mock sys.argv
       sys.argv = ['main.py', 'tests/fixtures/test_device_mib.xlsx']

       # Run main
       main()

       # Verify output exists
       import glob
       templates = glob.glob('created_templates/*.json')
       assert len(templates) > 0
   ```

## Debugging Tips

### Common Issues and Solutions

#### Import Errors

```python
# Problem: ModuleNotFoundError
# Solution: Check PYTHONPATH or use absolute imports
from utils.logger import logger  # Not: from logger import logger
```

#### Type Errors

```python
# Problem: Type mismatches
# Solution: Check pandas DataFrame vs dict vs list
print(type(data))  # Is it what you expect?
print(data.head() if isinstance(data, pd.DataFrame) else data)
```

#### Trigger Not Created

```python
# Debug trigger detection
from utils.trigger_detector import TriggerDetector

item_data = {'Name': 'cpuUtil', 'Type': 'GAUGE32', 'Description': 'CPU'}

# Check if should create
print(f"Should create: {TriggerDetector.should_create_trigger(item_data)}")

# Check analysis
result = TriggerDetector.analyze_item(item_data)
print(f"Analysis result: {result}")

# Check keyword matching
name_lower = item_data['Name'].lower()
matching = [kw for kw in TriggerDetector.UTILIZATION_KEYWORDS if kw in name_lower]
print(f"Matching keywords: {matching}")
```

#### Excel Reading Issues

```python
# Debug Excel extraction
import pandas as pd

file_path = 'sample_template_file.xlsx'

# Check sheets
xl_file = pd.ExcelFile(file_path)
print(f"Available sheets: {xl_file.sheet_names}")

# Read specific sheet
df = pd.read_excel(file_path, sheet_name='MIB Data')
print(f"Columns: {df.columns.tolist()}")
print(f"Shape: {df.shape}")
print(df.head())
```

### Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()

# Useful commands in pdb:
# n - next line
# s - step into function
# c - continue execution
# p variable_name - print variable
# l - list source code
# q - quit debugger
```

### Logging Best Practices

```python
from utils.logger import logger

# Use appropriate levels
logger.debug("Detailed information for debugging")
logger.info("General information about progress")
logger.warning("Something unexpected but not critical")
logger.error("Error occurred but execution continues")

# Include context in messages
logger.info(f"Creating trigger for item: {item_name}")
logger.warning(f"No enum data found for {item_name}, skipping value mapping")

# Log exceptions with traceback
try:
    risky_operation()
except Exception as e:
    logger.error(f"Failed to process item: {e}", exc_info=True)
```

## Pull Request Process

### Before Submitting

1. **Run all tests**:
   ```bash
   pytest tests/ -v --cov=. --cov-report=term-missing
   ```

2. **Check coverage** (should be ≥85%):
   ```bash
   # Overall coverage
   # Name                              Stmts   Miss  Cover
   # -----------------------------------------------------
   # utils/syntax_parser.py               84      6    93%
   # ...
   ```

3. **Update documentation**:
   - Add docstrings to new functions
   - Update README.md if user-facing changes
   - Update ARCHITECTURE.md if design changes

4. **Format code** (optional but recommended):
   ```bash
   # Using black
   pip install black
   black main.py utils/ zabbix_objects/

   # Using autopep8
   pip install autopep8
   autopep8 --in-place --recursive .
   ```

5. **Check for issues**:
   ```bash
   # Using flake8
   pip install flake8
   flake8 main.py utils/ zabbix_objects/
   ```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to not work)
- [ ] Documentation update

## Changes Made
- Added support for X
- Fixed issue with Y
- Updated Z documentation

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Coverage remains above 85%
- [ ] Manually tested with sample MIB file

## Related Issues
Closes #123

## Screenshots (if applicable)
```

### Review Process

1. **Automated checks** run on PR:
   - Tests must pass
   - No merge conflicts

2. **Code review** by maintainers:
   - Code quality
   - Test coverage
   - Documentation completeness

3. **Addressing feedback**:
   ```bash
   # Make requested changes
   git add .
   git commit -m "Address review feedback: fix xyz"
   git push origin feature/my-feature
   ```

4. **Merge**: Maintainer merges after approval

## Development Best Practices

### DO

✅ Write tests for new features
✅ Keep functions focused and small
✅ Use descriptive variable names
✅ Add docstrings to public functions
✅ Log important decisions and warnings
✅ Handle edge cases gracefully
✅ Keep backward compatibility when possible
✅ Update documentation with code changes

### DON'T

❌ Commit directly to main branch
❌ Push untested code
❌ Ignore test failures
❌ Use print() for debugging in production
❌ Hardcode configuration values
❌ Create overly complex functions (>50 lines)
❌ Leave commented-out code
❌ Ignore linter warnings

## Resources

### Zabbix Documentation

- [Zabbix 7.0 Template JSON Format](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/template)
- [SNMP Monitoring](https://www.zabbix.com/documentation/7.0/en/manual/config/items/itemtypes/snmp)
- [Low-Level Discovery](https://www.zabbix.com/documentation/7.0/en/manual/discovery/low_level_discovery)
- [Triggers](https://www.zabbix.com/documentation/7.0/en/manual/config/triggers)

### Python Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [pandas Documentation](https://pandas.pydata.org/docs/)

### Project Documentation

- [README.md](README.md) - User guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [CLAUDE.md](CLAUDE.md) - AI assistant guide

## Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers (see GitHub profile)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
