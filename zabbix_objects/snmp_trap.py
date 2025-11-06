import uuid
from typing import List, Dict, Any

from utils.config import SNMP_TRAP
from zabbix_objects.base import ZabbixObject

class SNMPTrap(ZabbixObject):
    def __init__(self, trap_data: Dict[str, Any], template_name: str):
        self.mib_module = trap_data.get('MIB Module')
        self.oid = trap_data.get('OID')
        self.raw_description = trap_data.get('Description')
        self.raw_name = trap_data.get('Name')
        self.raw_type = trap_data.get('Type')
        
        self.delay = SNMP_TRAP.DELAY
        self.history = SNMP_TRAP.HISTORY
        self.trends = SNMP_TRAP.TRENDS
        self.type = SNMP_TRAP.TYPE
        self.value_type = SNMP_TRAP.VALUE_TYPE

        # Use base class method and then remove ' Trap' suffix
        self.name = self._preprocess_name(self.raw_name).replace(' Trap', '')
        self.key = self._generate_key()
        self.description = self._preprocess_description()
        self.default_trigger = self._generate_default_trigger(template_name)

    @classmethod
    def generate_snmp_traps(cls, snmp_traps: List[Dict[str, Any]], template_name: str) -> List['SNMPTrap']:
        return [SNMPTrap(trap, template_name) for trap in snmp_traps]

    def _generate_key(self) -> str:
        return f'snmptrap["{self.oid}"]'

    def _generate_default_trigger(self, template_name: str) -> Dict[str, Any]:
        """
        Generate a default trigger for the SNMP trap.

        Args:
            template_name (str): Name of the template.

        Returns:
            Dict[str, Any]: Dictionary representing the default trigger.
        """
        default_trigger = {
                'description': self.description,
                'expression': f'length(last(/{template_name}/{self.key}))>0',
                'manual_close': SNMP_TRAP.TRIGGER.CLOSE,
                'name': self.name,
                'priority': SNMP_TRAP.TRIGGER.PRIORITY,
                'tags': [{'tag': 'snmp_trap', 'value': ''}],
                'type': SNMP_TRAP.TRIGGER.TYPE,
                'uuid': uuid.uuid4().hex,
                }
        return default_trigger

    def generate_json_dict(self) -> Dict[str, Any]:
        snmp_trap_json = {
            'delay': self.delay,
            'description': self.description,
            'history': self.history,
            'key': self.key,
            'name': self.name,
            'trends': self.trends,
            'triggers': [self.default_trigger],
            'type': self.type,
            'uuid': uuid.uuid4().hex,
            'value_type': self.value_type,
        }

        # Removes None/null values
        snmp_trap_json = {k: v for k, v in snmp_trap_json.items() if v is not None}

        return snmp_trap_json