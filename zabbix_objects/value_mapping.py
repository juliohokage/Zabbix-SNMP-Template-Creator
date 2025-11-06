import uuid
from typing import Dict, List, Any


class ValueMapping:
    """Zabbix value mapping for enum-based SNMP items."""

    def __init__(self, name: str, enums: List[Dict[str, str]]):
        """
        Initialize value mapping.

        Args:
            name: Name of the value mapping (usually the OID name)
            enums: List of enum dicts with 'value' and 'name' keys
        """
        self.name = name
        self.enums = enums
        self.uuid = uuid.uuid4().hex

    def generate_json_dict(self) -> Dict[str, Any]:
        """
        Generate Zabbix JSON representation of value mapping.

        Returns:
            Dictionary with 'uuid', 'name', and 'mappings' keys
        """
        mappings = []
        for enum in self.enums:
            mappings.append({
                'value': str(enum['value']),
                'newvalue': enum['name']
            })

        return {
            'uuid': self.uuid,
            'name': self.name,
            'mappings': mappings
        }

    @classmethod
    def generate_value_mappings(cls, items_with_enums: List[Dict[str, Any]]) -> List['ValueMapping']:
        """
        Generate value mappings for all items with enum data.

        Args:
            items_with_enums: List of dicts with 'name' and 'enum_data' keys

        Returns:
            List of ValueMapping objects
        """
        value_mappings = []

        for item in items_with_enums:
            name = item.get('name')
            enum_data = item.get('enum_data')

            if name and enum_data and enum_data.get('enums'):
                vm = cls(name, enum_data['enums'])
                value_mappings.append(vm)

        return value_mappings
