import re
from typing import Dict, List, Optional, Any
from utils.logger import logger


class SyntaxParser:
    """Parse MIB Syntax fields and extract enum values."""

    # Keywords indicating an "OK" or "normal" state
    OK_KEYWORDS = ['up', 'ok', 'normal', 'active', 'on', 'enabled', 'true', 'running', 'operational']

    # Keywords indicating a "BAD" or "problem" state
    BAD_KEYWORDS = ['down', 'error', 'failed', 'inactive', 'off', 'disabled', 'false', 'notpresent',
                    'unknown', 'warning', 'critical', 'dormant', 'testing', 'lowerlayerdown']

    @staticmethod
    def parse_syntax(syntax_string: str) -> Optional[Dict[str, Any]]:
        """
        Parse MIB Syntax field to extract enum values.

        Args:
            syntax_string: Syntax field from MIB (e.g., "INTEGER {up(1), down(2), testing(3)}")

        Returns:
            {
                'base_type': 'INTEGER',
                'enums': [
                    {'value': '1', 'name': 'up'},
                    {'value': '2', 'name': 'down'},
                    ...
                ]
            }
            or None if no enums found
        """
        if not syntax_string or pd.isna(syntax_string):
            return None

        syntax_string = str(syntax_string).strip()

        # Pattern: INTEGER {name1(value1), name2(value2), ...}
        # Also handles: BITS {name1(value1), name2(value2), ...}
        enum_pattern = r'(\w+)\s*\{([^}]+)\}'
        match = re.search(enum_pattern, syntax_string)

        if not match:
            return None

        base_type = match.group(1)
        enum_string = match.group(2)

        # Parse individual enums: name(value)
        enum_items = re.findall(r'(\w+)\s*\((\d+)\)', enum_string)

        if not enum_items:
            return None

        enums = [{'value': value, 'name': name} for name, value in enum_items]

        logger.debug(f"Parsed {len(enums)} enum values from Syntax: {base_type}")

        return {
            'base_type': base_type,
            'enums': enums
        }

    @staticmethod
    def parse_description_enums(description: str) -> Optional[List[Dict[str, str]]]:
        """
        Parse Description field for enum patterns when Syntax is missing.

        Args:
            description: Description text with enum patterns like "up(1) - powered on"

        Returns:
            [
                {'value': '1', 'name': 'up'},
                {'value': '2', 'name': 'down'},
                ...
            ]
            or None if no enums found
        """
        if not description or pd.isna(description):
            return None

        description = str(description)

        # Pattern: name(value) - description
        # Examples:
        #   "up(1) - powered on"
        #   "unknown(1) - unknown state"
        #   "down(2) - powered down"
        enum_pattern = r'(\w+)\s*\((\d+)\)\s*[-:]'
        matches = re.findall(enum_pattern, description, re.MULTILINE)

        if not matches or len(matches) < 2:  # Need at least 2 enums to be meaningful
            return None

        enums = [{'value': value, 'name': name} for name, value in matches]

        logger.debug(f"Parsed {len(enums)} enum values from Description")

        return enums

    @classmethod
    def identify_ok_value(cls, enums: List[Dict[str, str]]) -> Optional[str]:
        """
        Identify which enum value represents "OK" or "normal" state.

        Args:
            enums: List of enum dicts with 'value' and 'name' keys

        Returns:
            The enum value (as string) representing OK state, or None if can't determine
        """
        if not enums:
            return None

        # First pass: Look for explicit OK keywords
        for enum in enums:
            name_lower = enum['name'].lower()
            if any(keyword in name_lower for keyword in cls.OK_KEYWORDS):
                logger.debug(f"Identified OK value: {enum['value']} ({enum['name']})")
                return enum['value']

        # Second pass: If we have exactly 2 values, assume first is OK (common pattern)
        if len(enums) == 2:
            logger.debug(f"Binary enum detected, assuming first value is OK: {enums[0]['value']} ({enums[0]['name']})")
            return enums[0]['value']

        # Third pass: Exclude known bad states and pick first remaining
        good_enums = [e for e in enums
                      if not any(keyword in e['name'].lower() for keyword in cls.BAD_KEYWORDS)]

        if good_enums:
            logger.debug(f"Selected OK value by exclusion: {good_enums[0]['value']} ({good_enums[0]['name']})")
            return good_enums[0]['value']

        logger.warning(f"Could not determine OK value from enums: {[e['name'] for e in enums]}")
        return None

    @classmethod
    def identify_bad_values(cls, enums: List[Dict[str, str]], ok_value: Optional[str] = None) -> List[str]:
        """
        Identify which enum values represent "BAD" or "problem" states.

        Args:
            enums: List of enum dicts with 'value' and 'name' keys
            ok_value: The OK value to exclude (if known)

        Returns:
            List of enum values (as strings) representing bad states
        """
        if not enums:
            return []

        bad_values = []

        for enum in enums:
            # Skip the OK value
            if ok_value and enum['value'] == ok_value:
                continue

            name_lower = enum['name'].lower()

            # Check if name contains bad keywords
            if any(keyword in name_lower for keyword in cls.BAD_KEYWORDS):
                bad_values.append(enum['value'])

        logger.debug(f"Identified {len(bad_values)} bad values: {bad_values}")

        return bad_values

    @classmethod
    def extract_enum_data(cls, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract enum data from item, trying Syntax first, then Description.

        Args:
            item_data: Dictionary with 'Syntax', 'Description', 'Name' keys

        Returns:
            {
                'enums': [...],
                'ok_value': '1',
                'bad_values': ['2', '3'],
                'source': 'syntax' or 'description'
            }
            or None if no enums found
        """
        enums = None
        source = None

        # Try Syntax field first
        syntax_data = cls.parse_syntax(item_data.get('Syntax'))
        if syntax_data:
            enums = syntax_data['enums']
            source = 'syntax'

        # Fallback to Description if Syntax didn't work
        if not enums:
            enums = cls.parse_description_enums(item_data.get('Description'))
            if enums:
                source = 'description'

        if not enums:
            return None

        # Identify OK and bad values
        ok_value = cls.identify_ok_value(enums)
        bad_values = cls.identify_bad_values(enums, ok_value)

        return {
            'enums': enums,
            'ok_value': ok_value,
            'bad_values': bad_values,
            'source': source
        }


# Import pandas for isna check
import pandas as pd
