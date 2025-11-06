import uuid
from typing import List, Dict, Any

from utils.config import ITEM_PROTOTYPE, MAX_KEY_LENGTH
from utils.logger import logger
from zabbix_objects.base import ZabbixObject

class ItemPrototype(ZabbixObject):
    def __init__(self, item_data: Dict[str, Any], master_item_key: str, lld_macros: List[Dict[str, str]] = None):
        self.master_item = master_item_key
        self.mib_module = item_data.get('MIB Module')
        self.oid = item_data.get('OID')
        self.raw_description = item_data.get('Description')
        self.raw_name = item_data.get('Name')
        self.raw_type = item_data.get('Type')
        self.lld_macros = lld_macros or []

        self.history = ITEM_PROTOTYPE.HISTORY
        self.type = ITEM_PROTOTYPE.TYPE

        self.name = self._generate_name_with_macros()
        self.description = self._preprocess_description()
        self.key = self._generate_key(master_item_key)
        self.value_type = self._determine_value_type(self.raw_type)
        self.trends = self._determine_trends(self.value_type, ITEM_PROTOTYPE.TRENDS)

    @classmethod
    def generate_item_prototypes(cls, item_prototypes: List[Dict[str, Any]], template_name: str) -> List['ItemPrototype']:
        return [ItemPrototype(item, template_name) for item in item_prototypes]

    def _generate_name_with_macros(self) -> str:
        """
        Generate item prototype name with LLD macros.

        If LLD macros are available, format as: "{#MACRO1} {#MACRO2}: Item Name"
        Otherwise, use standard name processing.
        """
        base_name = self._preprocess_name(self.raw_name)

        if self.lld_macros:
            # Get macro names (without the path)
            macro_names = [m['lld_macro'] for m in self.lld_macros]
            macro_prefix = ' '.join(macro_names)
            return f"{macro_prefix}: {base_name}"

        return base_name

    def _generate_key(self, master_item_key: str) -> str:
        key_without_walk = master_item_key.replace(".walk", "")
        master_subkey = key_without_walk.split(".")[-1]
        item_name = self.name.replace(' ', '-').lower()
        final_item_name = item_name.replace(master_subkey, "")
        cleaned_name = final_item_name.replace("-", "")
        key = f"{key_without_walk}.{cleaned_name}[{{#SNMPINDEX}}]"

        if len(key) > MAX_KEY_LENGTH:
            logger.warning(f"Key '{key}' exceeds {MAX_KEY_LENGTH} characters and will be truncated.")
            return key[:MAX_KEY_LENGTH]

        return key

    def generate_json_dict(self) -> Dict[str, Any]:
        item_prototype_json = {
            'description': self.description,
            'history': self.history,
            'key': self.key,
            'master_item': {'key': self.master_item},
            'name': self.name,
            'trends': self.trends,
            'type': self.type,
            'uuid': uuid.uuid4().hex,
            'value_type': self.value_type,
        }

        # Removes None/null values
        item_prototype_json = {k: v for k, v in item_prototype_json.items() if v is not None}

        return item_prototype_json