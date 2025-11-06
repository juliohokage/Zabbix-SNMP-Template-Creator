import uuid
from typing import Dict, Any, List, Optional


class TriggerPrototype:
    """Zabbix trigger prototype for item prototypes in discovery rules."""

    # Severity mapping
    SEVERITY_MAP = {
        'INFO': '1',
        'WARNING': '2',
        'AVERAGE': '3',
        'HIGH': '4',
        'DISASTER': '5'
    }

    def __init__(self, item_proto_name: str, item_proto_key: str, template_name: str,
                 trigger_config: Dict[str, Any], lld_macros: List[Dict[str, str]]):
        """
        Initialize trigger prototype.

        Args:
            item_proto_name: Name of item prototype (may include LLD macros)
            item_proto_key: Key of item prototype
            template_name: Template name for expression
            trigger_config: Configuration from TriggerDetector
            lld_macros: List of LLD macro dicts from discovery rule
        """
        self.item_proto_name = item_proto_name
        self.item_proto_key = item_proto_key
        self.template_name = template_name
        self.config = trigger_config
        self.lld_macros = lld_macros

        self.name = self._generate_name()
        self.expression = self._generate_expression()
        self.severity = self._get_severity()
        self.description = self._generate_description()
        self.manual_close = trigger_config.get('manual_close', False)
        self.uuid = uuid.uuid4().hex

    def _generate_name(self) -> str:
        """
        Generate trigger prototype name with LLD macros.

        If LLD macros exist, prepend them to make trigger name specific.
        Example: "{#IFINDEX}: Interface is down"
        """
        description = self.config.get('description_template', f'{self.item_proto_name} issue')

        # If we have LLD macros, use first one in trigger name for specificity
        if self.lld_macros:
            first_macro = self.lld_macros[0]['lld_macro']
            # Check if description already contains macros
            if '{#' not in description:
                return f"{first_macro}: {description}"

        return description

    def _generate_description(self) -> str:
        """Generate trigger description with LLD macros and current value."""
        base_desc = self.config.get('description_template', f'{self.item_proto_name} issue')

        # Include all LLD macros in description for context
        if self.lld_macros and len(self.lld_macros) > 1:
            macro_str = ' '.join([m['lld_macro'] for m in self.lld_macros])
            base_desc = f"{macro_str}: {base_desc}"

        # Add macro info for threshold triggers
        if self.config.get('type') in ['threshold', 'rate']:
            macro_name = self.config.get('macro_name', '')
            return f"{base_desc} (current: {{ITEM.LASTVALUE}}, threshold: {macro_name})"

        return f"{base_desc} (current: {{ITEM.LASTVALUE}})"

    def _generate_expression(self) -> str:
        """
        Generate Zabbix trigger expression for item prototype.

        Returns:
            Expression like "count(/TEMPLATE/item.key,#3,"ne",{$MACRO})>=2"
        """
        macro_name = self.config.get('macro_name', '{$THRESHOLD}')

        # Build full item reference: /TemplateName/item.key
        item_ref = f"/{self.template_name}/{self.item_proto_key}"

        # Map expression types to actual Zabbix expressions
        trigger_type = self.config.get('type', 'state')

        if trigger_type == 'state':
            return f'count({item_ref},#3,"ne",{macro_name})>=2'

        elif trigger_type == 'threshold':
            return f'min({item_ref},5m)>{macro_name}'

        elif trigger_type == 'rate':
            return f'rate({item_ref},5m)>{macro_name}'

        else:
            return f'last({item_ref})<>{macro_name}'

    def _get_severity(self) -> str:
        """Get numeric severity code."""
        severity_name = self.config.get('severity', 'AVERAGE')
        return self.SEVERITY_MAP.get(severity_name, '3')  # Default to AVERAGE

    def generate_json_dict(self) -> Dict[str, Any]:
        """
        Generate Zabbix JSON representation of trigger prototype.

        Returns:
            Dictionary with trigger prototype properties
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
    def generate_trigger_prototypes(cls, item_protos_with_configs: list, template_name: str,
                                     lld_macros: List[Dict[str, str]]) -> list:
        """
        Generate trigger prototypes for item prototypes with trigger configs.

        Args:
            item_protos_with_configs: List of dicts with 'name', 'key', 'trigger_config'
            template_name: Template name
            lld_macros: LLD macros from discovery rule

        Returns:
            List of TriggerPrototype objects
        """
        trigger_prototypes = []

        for item_proto in item_protos_with_configs:
            item_name = item_proto.get('name')
            item_key = item_proto.get('key')
            trigger_config = item_proto.get('trigger_config')

            if item_name and item_key and trigger_config:
                trigger_proto = cls(item_name, item_key, template_name, trigger_config, lld_macros)
                trigger_prototypes.append(trigger_proto)

        return trigger_prototypes
