import re
from typing import Optional
from abc import ABC, abstractmethod


class ZabbixObject(ABC):
    """
    Base class for all Zabbix objects (SNMP Items, Traps, Item Prototypes).
    Provides shared functionality for name processing, description formatting,
    and value type determination.
    """

    @staticmethod
    def _preprocess_name(raw_name: str) -> str:
        """
        Preprocess MIB name to create a human-readable Zabbix item name.

        - Removes leading lowercase/non-letter characters
        - Adds spaces between camelCase words

        Args:
            raw_name: Raw name from MIB data

        Returns:
            Formatted name suitable for Zabbix display
        """
        name = re.sub(r'^[^A-Z]*', '', raw_name)
        return re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)

    def _preprocess_description(self) -> str:
        """
        Format MIB description for Zabbix item description field.

        - Adds MIB module and OID reference
        - Normalizes whitespace
        - Replaces single quotes with double quotes

        Returns:
            Formatted description with MIB metadata
        """
        if not self.raw_description:
            return f"{self.mib_module}::{self.raw_name}\nOID::{self.oid}\nNo description available."

        paragraphs = self.raw_description.split('\n\n')
        processed_paragraphs = []
        for paragraph in paragraphs:
            paragraph = re.sub(r'\s+', ' ', paragraph.strip())
            paragraph = paragraph.replace("'", '"')
            processed_paragraphs.append(paragraph)

        processed_description = '\n'.join(processed_paragraphs)

        return f"{self.mib_module}::{self.raw_name}\nOID::{self.oid}\n{processed_description}"

    @staticmethod
    def _determine_value_type(raw_type: str) -> Optional[str]:
        """
        Map SNMP/MIB data type to Zabbix value type.

        Args:
            raw_type: SNMP type from MIB (e.g., 'DISPLAYSTRING', 'Integer32', 'INTEGER32')

        Returns:
            Zabbix value type or None (uses Zabbix default numeric)

        Mapping:
            - String types (DISPLAYSTRING/OCTET STRING) → CHAR
            - Numeric integer types (INTEGER, Integer32, Unsigned32, GAUGE32, etc.) → None (numeric)
            - Float types → FLOAT
            - Everything else → TEXT
        """
        # Normalize to uppercase for case-insensitive matching
        raw_type_upper = raw_type.upper() if raw_type else ''

        # String types
        if raw_type_upper in ['DISPLAYSTRING', 'OCTET STRING', 'SNMPADMINSTRING']:
            return 'CHAR'

        # Numeric integer types - return None to use Zabbix default numeric type
        numeric_keywords = [
            'INTEGER', 'UNSIGNED', 'GAUGE', 'COUNTER', 'TIMETICKS', 'INTERFACEINDEX'
        ]
        if any(keyword in raw_type_upper for keyword in numeric_keywords):
            return None

        # Float types
        if 'FLOAT' in raw_type_upper or 'DOUBLE' in raw_type_upper:
            return 'FLOAT'

        # Default to TEXT for unknown types
        return 'TEXT'

    @staticmethod
    def _determine_trends(value_type: Optional[str], default_from_config: str) -> str:
        """
        Determine trends storage period based on value type.

        Only numeric types (FLOAT and None/Integer32) can have trends.
        Text/character types cannot have trends.

        Args:
            value_type: Zabbix value type (CHAR, TEXT, FLOAT, or None)
            default_from_config: Default trends period from config

        Returns:
            Trends period ('0' for non-numeric, config value for numeric)
        """
        if (value_type == 'FLOAT') or (value_type is None):
            return default_from_config
        else:
            return '0'

    @abstractmethod
    def generate_json_dict(self):
        """
        Generate JSON dictionary representation of this Zabbix object.
        Must be implemented by subclasses.
        """
        pass
