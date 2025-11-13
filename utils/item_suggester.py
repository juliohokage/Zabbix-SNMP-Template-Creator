"""
Item Suggester - Intelligent detection of SNMP items and traps from MIB data.

This module provides heuristics to automatically suggest which MIB objects should be
monitored as SNMP items or traps, reducing manual selection effort.
"""

from typing import List, Dict, Any
from utils.logger import logger


class ItemSuggester:
    """
    Analyzes MIB data and suggests SNMP items and traps based on intelligent heuristics.
    """

    # Access types that indicate readable SNMP items
    READABLE_ACCESS = {'read-only', 'read-write', 'read-create'}

    # Access types to exclude from items
    EXCLUDED_ACCESS = {'not-accessible', 'accessible-for-notify'}

    # Keywords that indicate table/structural elements (not monitorable items)
    TABLE_KEYWORDS = ['Table', 'Entry']

    # Types that indicate traps/notifications
    TRAP_TYPES = ['NOTIFICATION', 'TRAP']

    # Common important OID patterns to always include
    PRIORITY_PATTERNS = [
        'sysUpTime', 'sysName', 'sysDescr', 'sysContact', 'sysLocation',
        'ifOperStatus', 'ifAdminStatus', 'ifDescr', 'ifSpeed',
    ]

    # Keywords that suggest important monitoring items
    IMPORTANT_KEYWORDS = [
        'status', 'state', 'utilization', 'usage', 'temperature', 'temp',
        'cpu', 'memory', 'mem', 'error', 'fault', 'alarm', 'available',
        'capacity', 'threshold', 'power', 'voltage', 'fan', 'health'
    ]

    # Keywords that suggest informational (less critical) items
    INFORMATIONAL_KEYWORDS = [
        'serial', 'version', 'model', 'manufacturer', 'vendor', 'index',
        'port', 'label', 'name', 'descr', 'description'
    ]

    @classmethod
    def suggest_snmp_items(cls, mib_data: List[Dict[str, Any]],
                          include_informational: bool = True,
                          max_items: int = None) -> List[Dict[str, Any]]:
        """
        Suggest SNMP items from MIB data based on intelligent filtering.

        Args:
            mib_data: List of MIB data dictionaries
            include_informational: Whether to include informational items (serial numbers, etc.)
            max_items: Maximum number of items to suggest (None = unlimited)

        Returns:
            List of suggested SNMP item dictionaries, sorted by importance
        """
        suggested_items = []

        for entry in mib_data:
            # Skip if missing required fields
            if not entry.get('Name') or not entry.get('OID'):
                continue

            # Skip if it's a table or entry definition
            if cls._is_table_structure(entry):
                continue

            # Skip if it's a trap/notification
            if cls._is_trap(entry):
                continue

            # Skip if access type indicates it's not readable
            if not cls._is_readable(entry):
                continue

            # Skip informational items if requested
            if not include_informational and cls._is_informational(entry):
                continue

            # Calculate importance score
            importance = cls._calculate_importance(entry)
            entry_with_score = entry.copy()
            entry_with_score['_importance_score'] = importance

            suggested_items.append(entry_with_score)

        # Sort by importance (highest first)
        suggested_items.sort(key=lambda x: x['_importance_score'], reverse=True)

        # Limit if requested
        if max_items:
            suggested_items = suggested_items[:max_items]

        logger.info(f"Suggested {len(suggested_items)} SNMP items from {len(mib_data)} MIB entries")
        return suggested_items

    @classmethod
    def suggest_snmp_traps(cls, mib_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggest SNMP traps from MIB data.

        Args:
            mib_data: List of MIB data dictionaries

        Returns:
            List of suggested SNMP trap dictionaries
        """
        suggested_traps = []

        for entry in mib_data:
            # Skip if missing required fields
            if not entry.get('Name') or not entry.get('OID'):
                continue

            # Include if it's a trap/notification
            if cls._is_trap(entry):
                suggested_traps.append(entry)

        logger.info(f"Suggested {len(suggested_traps)} SNMP traps from {len(mib_data)} MIB entries")
        return suggested_traps

    @classmethod
    def categorize_items(cls, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize items into priority groups for better user selection.

        Args:
            items: List of item dictionaries

        Returns:
            Dictionary with categories: 'critical', 'important', 'informational'
        """
        categories = {
            'critical': [],
            'important': [],
            'informational': []
        }

        for item in items:
            score = item.get('_importance_score', 0)

            if score >= 10:
                categories['critical'].append(item)
            elif score >= 5:
                categories['important'].append(item)
            else:
                categories['informational'].append(item)

        return categories

    @staticmethod
    def _is_table_structure(entry: Dict[str, Any]) -> bool:
        """Check if entry is a table or entry definition."""
        name = entry.get('Name') or ''
        type_ = entry.get('Type') or ''

        # Check for table indicators
        if 'Table' in name and 'SEQUENCE OF' in type_:
            return True

        # Check for entry indicators (usually "Entry" suffix and specific types)
        if name.endswith('Entry') and 'Entry' in type_:
            return True

        return False

    @staticmethod
    def _is_trap(entry: Dict[str, Any]) -> bool:
        """Check if entry is a trap/notification."""
        type_ = (entry.get('Type') or '').upper()
        name = (entry.get('Name') or '').lower()

        # Check type field
        if 'NOTIFICATION' in type_ or 'TRAP' in type_:
            return True

        # Check name patterns
        if 'trap' in name or 'notification' in name:
            return True

        return False

    @classmethod
    def _is_readable(cls, entry: Dict[str, Any]) -> bool:
        """Check if entry has readable access."""
        access = (entry.get('Access') or '').lower()
        return access in cls.READABLE_ACCESS

    @classmethod
    def _is_informational(cls, entry: Dict[str, Any]) -> bool:
        """Check if entry is informational (serial number, description, etc.)."""
        name = (entry.get('Name') or '').lower()

        for keyword in cls.INFORMATIONAL_KEYWORDS:
            if keyword in name:
                return True

        return False

    @classmethod
    def _calculate_importance(cls, entry: Dict[str, Any]) -> int:
        """
        Calculate importance score for an item.

        Higher scores indicate more important monitoring items.
        Score ranges:
        - 15+: Critical system items (sysUpTime, etc.)
        - 10-14: High priority (status, errors, utilization)
        - 5-9: Medium priority (counters, metrics)
        - 0-4: Low priority (informational)
        """
        score = 0
        name = (entry.get('Name') or '').lower()

        # Priority patterns get highest score
        for pattern in cls.PRIORITY_PATTERNS:
            if pattern.lower() in name:
                score += 15
                return score  # Short circuit - these are always critical

        # Important keywords
        for keyword in cls.IMPORTANT_KEYWORDS:
            if keyword in name:
                score += 10
                break  # Only count once

        # Informational items get lower score
        if cls._is_informational(entry):
            score = max(score, 3)  # Cap at 3 unless already higher
        else:
            score += 5  # Non-informational items get base score

        return score

    @classmethod
    def get_statistics(cls, mib_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get statistics about MIB data composition.

        Args:
            mib_data: List of MIB data dictionaries

        Returns:
            Dictionary with counts of different object types
        """
        stats = {
            'total_entries': len(mib_data),
            'readable_items': 0,
            'traps': 0,
            'tables': 0,
            'not_accessible': 0,
            'critical_items': 0,
            'important_items': 0,
            'informational_items': 0
        }

        for entry in mib_data:
            if cls._is_table_structure(entry):
                stats['tables'] += 1
            elif cls._is_trap(entry):
                stats['traps'] += 1
            elif cls._is_readable(entry):
                stats['readable_items'] += 1

                # Calculate importance
                importance = cls._calculate_importance(entry)
                if importance >= 10:
                    stats['critical_items'] += 1
                elif importance >= 5:
                    stats['important_items'] += 1
                else:
                    stats['informational_items'] += 1
            else:
                stats['not_accessible'] += 1

        return stats
