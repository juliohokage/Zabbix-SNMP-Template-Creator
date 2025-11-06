from typing import Dict, Optional, Any, List
from utils.syntax_parser import SyntaxParser
from utils.logger import logger


class TriggerDetector:
    """Determine if and how to create triggers for SNMP items."""

    # Informational field keywords - SKIP triggers for these
    INFORMATIONAL_KEYWORDS = [
        'serial', 'descr', 'description', 'name', 'label', 'text',
        'version', 'model', 'manufacturer', 'location', 'contact',
        'alias', 'ident', 'string', 'comment', 'note', 'caption',
        'address', 'mac', 'ip', 'port', 'slot', 'index', 'number',
        'uptime', 'time', 'date', 'timestamp', 'age', 'lastchange'
    ]

    # Utilization/Percentage patterns
    UTILIZATION_KEYWORDS = [
        'util', 'usage', 'percent', 'cpu', 'load', 'busy', 'occupation'
    ]

    # Temperature patterns
    TEMPERATURE_KEYWORDS = [
        'temp', 'temperature', 'celsius', 'fahrenheit', 'thermal'
    ]

    # Error/Drop counter patterns
    ERROR_KEYWORDS = [
        'error', 'drop', 'discard', 'loss', 'collision', 'fail', 'bad',
        'corrupt', 'invalid', 'overflow', 'underrun', 'crc', 'fcs'
    ]

    # Memory patterns
    MEMORY_KEYWORDS = [
        'memory', 'mem', 'buffer', 'pool', 'heap', 'ram'
    ]

    # Status/State patterns (for enum-based triggers)
    STATUS_KEYWORDS = [
        'status', 'state', 'admin', 'oper', 'link', 'condition'
    ]

    @classmethod
    def should_create_trigger(cls, item_data: Dict[str, Any]) -> bool:
        """
        Determine if item should have a trigger.

        Conservative approach:
        1. Skip informational fields
        2. Only create for status/critical metrics

        Args:
            item_data: Dictionary with 'Name', 'Type', 'Description', etc.

        Returns:
            True if trigger should be created
        """
        name = item_data.get('Name', '').lower()
        item_type = item_data.get('Type', '').lower()

        # Skip informational fields
        if any(keyword in name for keyword in cls.INFORMATIONAL_KEYWORDS):
            logger.debug(f"Skipping trigger for informational field: {item_data.get('Name')}")
            return False

        # Skip text-only fields
        if item_type in ['displaystring', 'octet string', 'octetstring']:
            logger.debug(f"Skipping trigger for text field: {item_data.get('Name')}")
            return False

        return True

    @classmethod
    def analyze_item(cls, item_data: Dict[str, Any], enum_data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze item and return trigger configuration.

        Priority:
        1. Use enum data (from Syntax or Description) for state-based trigger
        2. Use pattern matching for utilization/temp/error counters
        3. Return None if informational or can't determine

        Args:
            item_data: Dictionary with item metadata
            enum_data: Optional pre-parsed enum data from SyntaxParser

        Returns:
            {
                'type': 'state' | 'threshold' | 'rate',
                'expression_template': 'count(#3,"ne",{$MACRO})>=2',
                'severity': 'AVERAGE',
                'ok_value': '1',  # For state triggers
                'macro_name': '{$ITEM.STATUS.OK}',
                'macro_value': '90',
                'description_template': 'Item is in bad state',
                'use_time_function': True
            }
            or None if trigger should not be created
        """
        # Check if we should create trigger at all
        if not cls.should_create_trigger(item_data):
            return None

        name = item_data.get('Name', '').lower()
        item_type = item_data.get('Type', '').lower()

        # Priority 1: Enum-based state trigger
        if enum_data and enum_data.get('enums'):
            return cls._create_state_trigger_config(item_data, enum_data)

        # Priority 2: Pattern-based triggers for critical metrics
        # Check utilization
        if any(keyword in name for keyword in cls.UTILIZATION_KEYWORDS):
            return cls._create_utilization_trigger_config(item_data)

        # Check temperature
        if any(keyword in name for keyword in cls.TEMPERATURE_KEYWORDS):
            return cls._create_temperature_trigger_config(item_data)

        # Check error counters
        if any(keyword in name for keyword in cls.ERROR_KEYWORDS):
            return cls._create_error_rate_trigger_config(item_data)

        # Check memory
        if any(keyword in name for keyword in cls.MEMORY_KEYWORDS):
            return cls._create_memory_trigger_config(item_data)

        # Check status (without enums - fallback)
        if any(keyword in name for keyword in cls.STATUS_KEYWORDS):
            return cls._create_generic_status_trigger_config(item_data)

        logger.debug(f"No trigger pattern matched for: {item_data.get('Name')}")
        return None

    @classmethod
    def _create_state_trigger_config(cls, item_data: Dict, enum_data: Dict) -> Dict[str, Any]:
        """Create trigger config for enum-based state fields."""
        item_name = item_data.get('Name', 'Unknown')
        ok_value = enum_data.get('ok_value', '1')

        # Generate macro name from item name
        macro_name = cls._generate_macro_name(item_name, 'STATUS.OK')

        return {
            'type': 'state',
            'expression_template': 'count(#3,"ne",{$MACRO})>=2',
            'severity': 'AVERAGE',
            'ok_value': ok_value,
            'macro_name': macro_name,
            'macro_value': ok_value,
            'description_template': f'{item_name} is not in operational state',
            'use_time_function': True
        }

    @classmethod
    def _create_utilization_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
        """Create trigger config for CPU/utilization metrics."""
        item_name = item_data.get('Name', 'Unknown')
        macro_name = cls._generate_macro_name(item_name, 'UTIL.MAX')

        return {
            'type': 'threshold',
            'expression_template': 'min(5m)>{$MACRO}',
            'severity': 'HIGH',
            'macro_name': macro_name,
            'macro_value': '90',
            'description_template': f'{item_name} is too high',
            'use_time_function': True
        }

    @classmethod
    def _create_temperature_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
        """Create trigger config for temperature sensors."""
        item_name = item_data.get('Name', 'Unknown')
        macro_name = cls._generate_macro_name(item_name, 'TEMP.MAX')

        return {
            'type': 'threshold',
            'expression_template': 'avg(5m)>{$MACRO}',
            'severity': 'HIGH',
            'macro_name': macro_name,
            'macro_value': '75',
            'description_template': f'{item_name} is too high',
            'use_time_function': True
        }

    @classmethod
    def _create_error_rate_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
        """Create trigger config for error counters."""
        item_name = item_data.get('Name', 'Unknown')
        macro_name = cls._generate_macro_name(item_name, 'RATE.MAX')

        return {
            'type': 'rate',
            'expression_template': 'rate(5m)>{$MACRO}',
            'severity': 'AVERAGE',
            'macro_name': macro_name,
            'macro_value': '10',
            'description_template': f'{item_name} rate is too high',
            'use_time_function': True
        }

    @classmethod
    def _create_memory_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
        """Create trigger config for memory usage."""
        item_name = item_data.get('Name', 'Unknown')
        macro_name = cls._generate_macro_name(item_name, 'UTIL.MAX')

        return {
            'type': 'threshold',
            'expression_template': 'min(5m)>{$MACRO}',
            'severity': 'HIGH',
            'macro_name': macro_name,
            'macro_value': '90',
            'description_template': f'{item_name} is too high',
            'use_time_function': True
        }

    @classmethod
    def _create_generic_status_trigger_config(cls, item_data: Dict) -> Dict[str, Any]:
        """Create generic status trigger when no enums available."""
        item_name = item_data.get('Name', 'Unknown')
        macro_name = cls._generate_macro_name(item_name, 'STATUS.OK')

        return {
            'type': 'state',
            'expression_template': 'count(#3,"ne",{$MACRO})>=2',
            'severity': 'WARNING',
            'ok_value': '1',  # Assume 1 is OK
            'macro_name': macro_name,
            'macro_value': '1',
            'description_template': f'{item_name} is not OK',
            'use_time_function': True
        }

    @staticmethod
    def _generate_macro_name(item_name: str, suffix: str) -> str:
        """
        Generate macro name from item name.

        Args:
            item_name: Original item name (e.g., "ifOperStatus", "cpuUtil5sec")
            suffix: Macro suffix (e.g., "STATUS.OK", "UTIL.MAX")

        Returns:
            Macro name like "{$IFOPERSTATUS.STATUS.OK}" or "{$CPU.UTIL.MAX}"
        """
        # Remove common prefixes
        clean_name = item_name
        for prefix in ['cisco', 'ent', 'if', 'ospfv3', 'snmp']:
            if clean_name.lower().startswith(prefix):
                clean_name = clean_name[len(prefix):]
                break

        # Convert to uppercase and remove special chars
        clean_name = ''.join(c if c.isalnum() else '' for c in clean_name)
        clean_name = clean_name.upper()

        # Limit length
        if len(clean_name) > 20:
            clean_name = clean_name[:20]

        return f"{{${clean_name}.{suffix}}}"
