import uuid
from typing import List, Dict, Any

from utils.config import SNMP_ITEM, MAX_KEY_LENGTH
from utils.logger import logger
from zabbix_objects.base import ZabbixObject

class SNMPItem(ZabbixObject):
    def __init__(self, item_data: Dict[str, Any], template_name: str):
        self.mib_module = item_data.get('MIB Module')
        self.oid = item_data.get('OID')
        self.raw_description = item_data.get('Description')
        self.raw_name = item_data.get('Name')
        self.raw_type = item_data.get('Type')

        self.delay = SNMP_ITEM.DELAY
        self.history = SNMP_ITEM.HISTORY
        self.type = SNMP_ITEM.TYPE

        self.name = self._preprocess_name(self.raw_name)
        self.description = self._preprocess_description()
        self.key = self._generate_key(template_name)
        self.value_type = self._determine_value_type(self.raw_type)
        self.snmp_oid = self._generate_snmp_oid()
        self.trends = self._determine_trends(self.value_type, SNMP_ITEM.TRENDS)

    @classmethod
    def generate_snmp_items(cls, snmp_items: List[Dict[str, Any]], template_name: str) -> List['SNMPItem']:
        return [SNMPItem(item, template_name) for item in snmp_items]

    def _generate_snmp_oid(self) -> str:
        return f'get[{self.oid}]'

    def _generate_key(self, template_name: str) -> str:
        item_name = self.name.replace(' ', '-').lower()
        template_part = template_name.lower().replace(' ', '.')
        key = f'{template_part}.{item_name}.get'

        if len(key) > MAX_KEY_LENGTH:
            logger.warning(f"Key '{key}' exceeds {MAX_KEY_LENGTH} characters and will be truncated.")
            return key[:MAX_KEY_LENGTH]

        return key

    def generate_json_dict(self) -> Dict[str, Any]:
        snmp_item_json = {
            'description': self.description,
            'history': self.history,
            'delay': self.delay,
            'key': self.key,
            'name': self.name,
            'snmp_oid': self.oid,
            'trends': self.trends,
            'type': self.type,
            'uuid': uuid.uuid4().hex,
            'value_type': self.value_type,
        }

        # Removes None/null values
        snmp_item_json = {k: v for k, v in snmp_item_json.items() if v is not None}

        return snmp_item_json
