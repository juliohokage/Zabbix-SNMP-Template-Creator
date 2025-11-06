import uuid
from typing import List, Dict, Any, Optional

from zabbix_objects.snmp_walk_item import SNMPWalkItem
from zabbix_objects.item_prototype import ItemPrototype
from zabbix_objects.trigger_prototype import TriggerPrototype
from utils.config import DISCOVERY_RULE
from utils.index_detector import detect_index_oids, create_lld_macros
from utils.syntax_parser import SyntaxParser
from utils.trigger_detector import TriggerDetector
from utils.logger import logger

class DiscoveryRule:
    def __init__(self, discovery_rule_table: List[Dict[str, Any]], template_name: str, table_key: Optional[str] = None,
                 generate_triggers: bool = True, trigger_overrides: Optional[Dict[str, Dict]] = None):
        self.type = DISCOVERY_RULE.TYPE
        self.table_key = table_key
        self.template_name = template_name
        self.generate_triggers = generate_triggers
        self.trigger_overrides = trigger_overrides or {}

        # Detect index OIDs and create LLD macros
        self.lld_macros = []
        if len(discovery_rule_table) > 2:  # Has columns beyond Table and Entry
            index_oids = detect_index_oids(discovery_rule_table)
            self.lld_macros = create_lld_macros(index_oids)

        self.snmp_walk_item = SNMPWalkItem(discovery_rule_table, template_name, table_key)
        self.master_item = self.snmp_walk_item.key
        self.key = self._generate_key()
        self.description = self._generate_description()
        self.name = self._generate_name()

        # Generate item prototypes
        self.item_prototypes = self._generate_item_prototypes(self.master_item, discovery_rule_table)

        # Generate trigger prototypes if enabled
        self.trigger_prototypes = []
        if self.generate_triggers:
            self.trigger_prototypes = self._generate_trigger_prototypes()

    def _generate_name(self) -> str:
        name = self.snmp_walk_item.name
        return name.replace('Walk', 'Discovery')

    def _generate_key(self) -> str:
        master_item_key = self.snmp_walk_item.key
        return master_item_key.replace("walk", "discovery")

    def _generate_description(self) -> str:
        return self.snmp_walk_item.description

    @classmethod
    def generate_discovery_rules(cls, discovery_rule_table: Dict[str, List[Dict[str, Any]]], template_name: str,
                                 generate_triggers: bool = True, trigger_overrides: Optional[Dict[str, Dict]] = None) -> List['DiscoveryRule']:
        return [DiscoveryRule(table_data, template_name, table_key, generate_triggers, trigger_overrides)
                for table_key, table_data in discovery_rule_table.items()]

    def _generate_item_prototypes(self, master_item_key: str, discovery_rule_table: List[Dict[str, Any]]) -> List[ItemPrototype]:
        """Generate item prototypes with enum data and trigger configs."""
        item_prototypes = []
        seen_keys = set()  # Track keys to avoid duplicates from split discovery rules

        # Start at 2nd index in DiscoveryRuleTable b/c the 1st entry will always be the master item
        for entry in discovery_rule_table[1:]:
            item_name = entry.get('Name')

            # Extract enum data from Syntax or Description
            enum_data = SyntaxParser.extract_enum_data(entry)

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
                        logger.debug(f"Using trigger override for item prototype: {item_name}")
                else:
                    # Auto-detect trigger
                    trigger_config = TriggerDetector.analyze_item(entry, enum_data)
                    if trigger_config:
                        logger.debug(f"Auto-generated trigger for item prototype: {item_name}")

            item_proto = ItemPrototype(entry, master_item_key, self.lld_macros,
                                      value_mapping_name, enum_data, trigger_config)

            # Skip if we've already added an item with this key (handles split discovery rules)
            if item_proto.key in seen_keys:
                logger.debug(f"Skipping duplicate item prototype key: {item_proto.key}")
                continue

            seen_keys.add(item_proto.key)
            item_prototypes.append(item_proto)

        return item_prototypes

    def _generate_trigger_prototypes(self) -> List[TriggerPrototype]:
        """Generate trigger prototypes for item prototypes that have trigger configs."""
        trigger_prototypes = []

        for item_proto in self.item_prototypes:
            if item_proto.trigger_config:
                # Validate trigger compatibility with value type
                trigger_type = item_proto.trigger_config.get('type')
                value_type = item_proto.value_type

                # min(), max(), avg(), rate() require numeric types
                # TEXT and CHAR are not numeric
                if trigger_type in ['threshold', 'rate'] and value_type in ['TEXT', 'CHAR']:
                    logger.warning(
                        f"Skipping {trigger_type} trigger for '{item_proto.name}': "
                        f"incompatible value_type '{value_type}' (SNMP type: {item_proto.raw_type})"
                    )
                    continue

                trigger_proto = TriggerPrototype(
                    item_proto.name,
                    item_proto.key,
                    self.template_name,
                    item_proto.trigger_config,
                    self.lld_macros
                )
                trigger_prototypes.append(trigger_proto)

        logger.debug(f"Generated {len(trigger_prototypes)} trigger prototypes for discovery rule: {self.name}")
        return trigger_prototypes

    def generate_json_dict(self) -> Dict[str, Any]:
        """
        Generate a dictionary that represents the discovery rule in JSON format.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representation of the discovery rule.
        """
        discovery_rule_json = {
            'description': self.description,
            'key': self.key,
            'master_item': {'key': self.master_item},
            'name': self.name,
            'type': self.type,
            'uuid': uuid.uuid4().hex,
        }

        # Add LLD macro paths if available
        if self.lld_macros:
            discovery_rule_json['lld_macro_paths'] = self.lld_macros

        item_prototype_json = [item_prototype.generate_json_dict() for item_prototype in self.item_prototypes]

        if item_prototype_json:
            discovery_rule_json['item_prototypes'] = item_prototype_json

        # Add trigger prototypes if available
        if self.trigger_prototypes:
            trigger_prototype_json = [trigger.generate_json_dict() for trigger in self.trigger_prototypes]
            discovery_rule_json['trigger_prototypes'] = trigger_prototype_json

        # Removes None/null values
        discovery_rule_json = {k: v for k, v in discovery_rule_json.items() if v is not None}

        return discovery_rule_json
