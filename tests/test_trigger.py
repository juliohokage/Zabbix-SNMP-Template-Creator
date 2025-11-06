"""Unit tests for zabbix_objects/trigger.py"""
import pytest
from zabbix_objects.trigger import Trigger


class TestTrigger:
    """Tests for Trigger class."""

    def test_create_state_trigger(self):
        """Test creating a state-based trigger."""
        trigger_config = {
            'type': 'state',
            'expression_template': 'count(#3,"ne",{$MACRO})>=2',
            'severity': 'AVERAGE',
            'ok_value': '1',
            'macro_name': '{$IFOPERSTATUS.STATUS.OK}',
            'macro_value': '1',
            'description_template': 'Interface status is down'
        }

        trigger = Trigger('If Oper Status', 'if.oper-status.get', 'Test Template', trigger_config)

        assert trigger.name == 'Interface status is down'
        assert trigger.severity == '3'  # AVERAGE = 3
        assert '{$IFOPERSTATUS.STATUS.OK}' in trigger.expression

    def test_create_utilization_trigger(self):
        """Test creating a utilization threshold trigger."""
        trigger_config = {
            'type': 'threshold',
            'severity': 'HIGH',
            'macro_name': '{$CPU.UTIL.MAX}',
            'macro_value': '90',
            'description_template': 'CPU utilization is too high'
        }

        trigger = Trigger('CPU Util', 'cpu.util.get', 'Test Template', trigger_config)

        assert 'min(' in trigger.expression
        assert '5m)>' in trigger.expression
        assert '{$CPU.UTIL.MAX}' in trigger.expression
        assert trigger.severity == '4'  # HIGH = 4

    def test_generate_json_dict(self):
        """Test generating JSON dict from trigger."""
        trigger_config = {
            'type': 'state',
            'severity': 'WARNING',
            'macro_name': '{$TEST.OK}',
            'macro_value': '1',
            'description_template': 'Test trigger'
        }

        trigger = Trigger('Test', 'test.key', 'Template', trigger_config)
        result = trigger.generate_json_dict()

        assert 'uuid' in result
        assert 'expression' in result
        assert 'name' in result
        assert 'priority' in result
        assert result['priority'] == '2'  # WARNING = 2

    def test_severity_mapping(self):
        """Test severity name to code mapping."""
        severities = {
            'INFO': '1',
            'WARNING': '2',
            'AVERAGE': '3',
            'HIGH': '4',
            'DISASTER': '5'
        }

        for sev_name, expected_code in severities.items():
            config = {'type': 'state', 'severity': sev_name, 'macro_name': '{$TEST}', 'macro_value': '1', 'description_template': 'Test'}
            trigger = Trigger('Test', 'test', 'Template', config)
            assert trigger.severity == expected_code

    def test_expression_with_template_name(self):
        """Test that expression includes template name."""
        trigger_config = {
            'type': 'state',
            'severity': 'WARNING',
            'macro_name': '{$TEST.OK}',
            'macro_value': '1',
            'description_template': 'Test'
        }

        trigger = Trigger('Test', 'test.key', 'My Test Template', trigger_config)

        assert '/My Test Template/' in trigger.expression
        assert '/test.key' in trigger.expression

    def test_generate_triggers_class_method(self):
        """Test generating multiple triggers."""
        items_with_configs = [
            {
                'name': 'Status 1',
                'key': 'status1.get',
                'trigger_config': {
                    'type': 'state',
                    'severity': 'AVERAGE',
                    'macro_name': '{$STATUS1.OK}',
                    'macro_value': '1',
                    'description_template': 'Status 1 issue'
                }
            },
            {
                'name': 'Status 2',
                'key': 'status2.get',
                'trigger_config': {
                    'type': 'state',
                    'severity': 'HIGH',
                    'macro_name': '{$STATUS2.OK}',
                    'macro_value': '1',
                    'description_template': 'Status 2 issue'
                }
            }
        ]

        triggers = Trigger.generate_triggers(items_with_configs, 'Template')

        assert len(triggers) == 2
        assert all(isinstance(t, Trigger) for t in triggers)
