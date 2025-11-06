import uuid
from typing import Dict, Any, Optional
from utils.config import TRIGGER


class Trigger:
    """Zabbix trigger for SNMP items."""

    # Severity mapping - Zabbix 7.0 uses string names, not numeric values
    SEVERITY_MAP = {
        'INFO': 'INFO',
        'WARNING': 'WARNING',
        'AVERAGE': 'AVERAGE',
        'HIGH': 'HIGH',
        'DISASTER': 'DISASTER'
    }

    def __init__(self, item_name: str, item_key: str, template_name: str, trigger_config: Dict[str, Any]):
        """
        Initialize trigger.

        Args:
            item_name: Name of the item (e.g., "If Oper Status")
            item_key: Key of the item (e.g., "cisco.catalyst.if-oper-status.get")
            template_name: Template name for expression
            trigger_config: Configuration from TriggerDetector
        """
        self.item_name = item_name
        self.item_key = item_key
        self.template_name = template_name
        self.config = trigger_config

        self.name = self._generate_name()
        self.expression = self._generate_expression()
        self.severity = self._get_severity()
        self.description = self._generate_description()
        self.manual_close = trigger_config.get('manual_close', False)
        self.uuid = uuid.uuid4().hex

    def _generate_name(self) -> str:
        """Generate trigger name from item name and config."""
        description = self.config.get('description_template', f'{self.item_name} issue')
        return description

    def _generate_description(self) -> str:
        """Generate trigger description with more details."""
        base_desc = self.config.get('description_template', f'{self.item_name} issue')

        # Add macro info for threshold triggers
        if self.config.get('type') in ['threshold', 'rate']:
            macro_name = self.config.get('macro_name', '')
            return f"{base_desc} (current value: {{ITEM.LASTVALUE}}, threshold: {macro_name})"

        return f"{base_desc} (current value: {{ITEM.LASTVALUE}})"

    def _generate_expression(self) -> str:
        """
        Generate Zabbix trigger expression.

        Returns:
            Expression like "count(/TEMPLATE/item.key,#3,"ne",{$MACRO})>=2"
        """
        expression_template = self.config.get('expression_template', 'last()=0')
        macro_name = self.config.get('macro_name', '{$THRESHOLD}')

        # Build full item reference: /TemplateName/item.key
        item_ref = f"/{self.template_name}/{self.item_key}"

        # Replace placeholders in template
        expression = expression_template.replace('{$MACRO}', macro_name)

        # Map expression types to actual Zabbix expressions
        trigger_type = self.config.get('type', 'state')

        if trigger_type == 'state':
            # count(/template/item.key,#3,"ne",{$MACRO})>=2
            return f'count({item_ref},#3,"ne",{macro_name})>=2'

        elif trigger_type == 'threshold':
            # min(/template/item.key,5m)>{$MACRO}
            return f'min({item_ref},5m)>{macro_name}'

        elif trigger_type == 'rate':
            # rate(/template/item.key,5m)>{$MACRO}
            return f'rate({item_ref},5m)>{macro_name}'

        else:
            # Fallback: last(/template/item.key)<>{$MACRO}
            return f'last({item_ref})<>{macro_name}'

    def _get_severity(self) -> str:
        """Get severity string name."""
        severity_name = self.config.get('severity', 'AVERAGE')
        return self.SEVERITY_MAP.get(severity_name, 'AVERAGE')  # Default to AVERAGE

    def generate_json_dict(self) -> Dict[str, Any]:
        """
        Generate Zabbix JSON representation of trigger.

        Returns:
            Dictionary with trigger properties
        """
        trigger_json = {
            'uuid': self.uuid,
            'expression': self.expression,
            'name': self.name,
            'priority': self.severity,
            'description': self.description,
        }

        # Add optional fields
        if self.manual_close:
            trigger_json['manual_close'] = '1'

        # Remove None/null values
        trigger_json = {k: v for k, v in trigger_json.items() if v is not None}

        return trigger_json

    @classmethod
    def generate_triggers(cls, items_with_configs: list, template_name: str) -> list:
        """
        Generate triggers for all items with trigger configs.

        Args:
            items_with_configs: List of dicts with 'name', 'key', 'trigger_config'
            template_name: Template name

        Returns:
            List of Trigger objects
        """
        triggers = []

        for item in items_with_configs:
            item_name = item.get('name')
            item_key = item.get('key')
            trigger_config = item.get('trigger_config')

            if item_name and item_key and trigger_config:
                trigger = cls(item_name, item_key, template_name, trigger_config)
                triggers.append(trigger)

        return triggers
