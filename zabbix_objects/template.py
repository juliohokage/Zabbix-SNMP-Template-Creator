import uuid
import concurrent.futures
from typing import List, Dict, Any, Optional

from zabbix_objects.snmp_item import SNMPItem
from zabbix_objects.snmp_trap import SNMPTrap
from zabbix_objects.tag import Tag
from zabbix_objects.discovery_rule import DiscoveryRule
from zabbix_objects.value_mapping import ValueMapping
from zabbix_objects.trigger import Trigger
from utils.syntax_parser import SyntaxParser
from utils.trigger_detector import TriggerDetector
from utils.logger import logger

class Template:
    def __init__(self, template_info_json: Dict[str, Any], snmp_item_json_list: List[Dict[str, Any]],
                 snmp_trap_json_list: List[Dict[str, Any]], discovery_rule_tables: Dict[str, List[Dict[str, Any]]],
                 generate_triggers: bool = True, trigger_overrides: Optional[Dict[str, Dict]] = None):
        self.group = template_info_json.get('Group')
        self.macros = template_info_json.get('Macros')
        self.manufacturer = template_info_json.get('Manufacturer')
        self.model = template_info_json.get('Model')
        self.raw_tags = template_info_json.get('Tags')
        self.device = template_info_json.get('Device')
        self.generate_triggers = generate_triggers
        self.trigger_overrides = trigger_overrides or {}

        self.name = self._generate_template_name()

        self.template_tags = Tag.generate_template_tags(self.raw_tags, self.manufacturer, self.device)

        # Generate SNMP items with enum/trigger analysis
        self.snmp_items = self._generate_enriched_snmp_items(snmp_item_json_list)

        # Generate SNMP traps (no triggers for traps)
        self.snmp_traps = SNMPTrap.generate_snmp_traps(snmp_trap_json_list, self.name)

        # Generate discovery rules with triggers
        self.discovery_rules = DiscoveryRule.generate_discovery_rules(
            discovery_rule_tables, self.name, generate_triggers, self.trigger_overrides
        )

        # Add walk items from discovery rules to items list
        for discovery_rule in self.discovery_rules:
            if discovery_rule.snmp_walk_item:
                self.snmp_items.append(discovery_rule.snmp_walk_item)

        # Generate value mappings from all items with enums
        self.value_mappings = self._generate_value_mappings()

        # Generate triggers for SNMP items
        self.triggers = []
        if self.generate_triggers:
            self.triggers = self._generate_triggers()

        self.mib_modules = self._get_mib_modules()
        self.description = self._preprocess_description()

    def _generate_template_name(self) -> str:
        return f"{self.manufacturer} {self.device} {self.model}"

    def _get_mib_modules(self) -> List[str]:
        """
        Get the list of MIB modules used in the template.

        Returns:
            List[str]: List of MIB module names.
        """
        mib_modules = set()
        for entry in (self.snmp_items or []) + (self.snmp_traps or []):
            if mib_module := entry.mib_module:
                mib_modules.add(mib_module)

        return list(mib_modules) or ["N/A"]
    
    def _preprocess_description(self) -> str:
        return f"Template {self.name}\nMIB(s) used:" + "\n".join(f"- {mib}" for mib in self.mib_modules)

    def _generate_enriched_snmp_items(self, snmp_item_json_list: List[Dict[str, Any]]) -> List[SNMPItem]:
        """Generate SNMP items with enum data and trigger configs."""
        snmp_items = []

        for item_data in snmp_item_json_list:
            item_name = item_data.get('Name')

            # Extract enum data from Syntax or Description
            enum_data = SyntaxParser.extract_enum_data(item_data)

            # Determine value mapping name if enums exist
            value_mapping_name = item_name if enum_data else None

            # Analyze for trigger generation
            trigger_config = None
            if self.generate_triggers:
                # Check for override first
                if item_name in self.trigger_overrides:
                    override = self.trigger_overrides[item_name]
                    if override.get('enabled', True):
                        trigger_config = override
                        logger.debug(f"Using trigger override for SNMP item: {item_name}")
                else:
                    # Auto-detect trigger
                    trigger_config = TriggerDetector.analyze_item(item_data, enum_data)
                    if trigger_config:
                        logger.debug(f"Auto-generated trigger for SNMP item: {item_name}")

            snmp_item = SNMPItem(item_data, self.name, value_mapping_name, enum_data, trigger_config)
            snmp_items.append(snmp_item)

        return snmp_items

    def _generate_value_mappings(self) -> List[ValueMapping]:
        """Generate value mappings from all items with enum data."""
        value_mappings = []
        seen_mappings = set()

        # Collect from SNMP items
        for item in self.snmp_items:
            if hasattr(item, 'enum_data') and item.enum_data and hasattr(item, 'value_mapping_name') and item.value_mapping_name:
                if item.value_mapping_name not in seen_mappings:
                    vm = ValueMapping(item.value_mapping_name, item.enum_data['enums'])
                    value_mappings.append(vm)
                    seen_mappings.add(item.value_mapping_name)

        # Collect from item prototypes in discovery rules
        for dr in self.discovery_rules:
            for item_proto in dr.item_prototypes:
                if item_proto.enum_data and item_proto.value_mapping_name:
                    if item_proto.value_mapping_name not in seen_mappings:
                        vm = ValueMapping(item_proto.value_mapping_name, item_proto.enum_data['enums'])
                        value_mappings.append(vm)
                        seen_mappings.add(item_proto.value_mapping_name)

        logger.info(f"Generated {len(value_mappings)} value mappings")
        return value_mappings

    def _generate_triggers(self) -> List[Trigger]:
        """Generate triggers for SNMP items that have trigger configs."""
        triggers = []

        for item in self.snmp_items:
            if hasattr(item, 'trigger_config') and item.trigger_config:
                trigger = Trigger(item.name, item.key, self.name, item.trigger_config)
                triggers.append(trigger)

        logger.info(f"Generated {len(triggers)} triggers for SNMP items")
        return triggers

    def _generate_trigger_macros(self) -> List[Dict[str, str]]:
        """Generate macros for all triggers."""
        trigger_macros = []
        seen_macros = set()

        # Collect from SNMP item triggers
        for item in self.snmp_items:
            if hasattr(item, 'trigger_config') and item.trigger_config:
                macro_name = item.trigger_config.get('macro_name')
                macro_value = item.trigger_config.get('macro_value')
                if macro_name and macro_name not in seen_macros:
                    trigger_macros.append({
                        'macro': macro_name,
                        'value': str(macro_value)
                    })
                    seen_macros.add(macro_name)

        # Collect from item prototype triggers in discovery rules
        for dr in self.discovery_rules:
            for item_proto in dr.item_prototypes:
                if item_proto.trigger_config:
                    macro_name = item_proto.trigger_config.get('macro_name')
                    macro_value = item_proto.trigger_config.get('macro_value')
                    if macro_name and macro_name not in seen_macros:
                        trigger_macros.append({
                            'macro': macro_name,
                            'value': str(macro_value)
                        })
                        seen_macros.add(macro_name)

        if trigger_macros:
            logger.info(f"Generated {len(trigger_macros)} trigger macros")

        return trigger_macros

    def _parse_macros(self) -> List[Dict[str, str]]:
        """
        Parse macros from template information.

        Expected format in Excel: {$MACRO1:value1},{$MACRO2:value2}
        or {$MACRO1}:value1,{$MACRO2}:value2

        Returns:
            List of macro dictionaries with 'macro' and 'value' keys
        """
        if not self.macros:
            return []

        macro_list = []
        # Split by comma
        macro_entries = [m.strip() for m in str(self.macros).split(',')]

        for entry in macro_entries:
            if ':' in entry:
                # Format: {$MACRO}:value or {$MACRO:value}
                if entry.startswith('{$') and '}:' in entry:
                    # {$MACRO}:value
                    parts = entry.split('}:', 1)
                    macro_name = parts[0] + '}'
                    macro_value = parts[1] if len(parts) > 1 else ''
                elif '{$' in entry and ':' in entry:
                    # {$MACRO:value}
                    macro_name = entry[:entry.rindex('}') + 1]
                    macro_value = entry[entry.rindex(':') + 1:].strip('}')
                else:
                    continue

                macro_list.append({
                    'macro': macro_name,
                    'value': macro_value
                })

        return macro_list

    def generate_json_dict(self) -> Dict[str, Any]:
        inner_json_structure = {
            'uuid': str(uuid.uuid4().hex),
            'template': self.name,
            'name': self.name,
            'description': self.description,
            'groups': [{'name': self.group}],
            'items': []
        }

        template_tag_json = [ tag.generate_json_dict() for tag in self.template_tags]
        if template_tag_json:
            inner_json_structure['tags'] = template_tag_json

        # Add macros (from template info + auto-generated trigger macros)
        template_macros = self._parse_macros()
        trigger_macros = self._generate_trigger_macros()
        all_macros = template_macros + trigger_macros
        if all_macros:
            inner_json_structure['macros'] = all_macros

        # Add value mappings
        if self.value_mappings:
            valuemap_json = [vm.generate_json_dict() for vm in self.value_mappings]
            inner_json_structure['valuemaps'] = valuemap_json

        # Template-level triggers are disabled for Zabbix 7.0 compatibility
        # Zabbix 7.0 import fails with "unexpected tag 'triggers'" error when triggers
        # are present at the template level. Trigger prototypes within discovery rules
        # continue to work correctly. Users can manually create triggers for standalone
        # items after importing the template if needed.
        #
        # Reference: https://github.com/juliohokage/Zabbix-SNMP-Template-Creator/issues/
        # if self.triggers:
        #     trigger_json = [trigger.generate_json_dict() for trigger in self.triggers]
        #     inner_json_structure['triggers'] = trigger_json

        outer_json_structure = {
            'zabbix_export': {
                'version': '7.0',
                'template_groups': [
                    {
                        'uuid': str(uuid.uuid4().hex),
                        'name': self.group
                    }
                ],
                'templates': [inner_json_structure]
            }
        }

        return outer_json_structure
