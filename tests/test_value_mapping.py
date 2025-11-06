"""Unit tests for zabbix_objects/value_mapping.py"""
import pytest
from zabbix_objects.value_mapping import ValueMapping


class TestValueMapping:
    """Tests for ValueMapping class."""

    def test_create_value_mapping(self):
        """Test creating a value mapping."""
        enums = [
            {'value': '1', 'name': 'up'},
            {'value': '2', 'name': 'down'}
        ]
        vm = ValueMapping('ifOperStatus', enums)

        assert vm.name == 'ifOperStatus'
        assert vm.enums == enums
        assert vm.uuid is not None

    def test_generate_json_dict(self):
        """Test generating JSON dict from value mapping."""
        enums = [
            {'value': '1', 'name': 'up'},
            {'value': '2', 'name': 'down'},
            {'value': '3', 'name': 'testing'}
        ]
        vm = ValueMapping('ifOperStatus', enums)

        result = vm.generate_json_dict()

        assert result['name'] == 'ifOperStatus'
        assert 'uuid' in result
        assert 'mappings' in result
        assert len(result['mappings']) == 3

    def test_json_dict_mapping_format(self):
        """Test that mappings are in correct format."""
        enums = [
            {'value': '1', 'name': 'normal'},
            {'value': '2', 'name': 'warning'}
        ]
        vm = ValueMapping('status', enums)

        result = vm.generate_json_dict()
        mappings = result['mappings']

        # Check first mapping format
        assert mappings[0]['value'] == '1'
        assert mappings[0]['newvalue'] == 'normal'
        assert mappings[1]['value'] == '2'
        assert mappings[1]['newvalue'] == 'warning'

    def test_value_as_string(self):
        """Test that values are converted to strings."""
        enums = [
            {'value': 1, 'name': 'up'},  # Integer value
            {'value': '2', 'name': 'down'}  # String value
        ]
        vm = ValueMapping('test', enums)

        result = vm.generate_json_dict()
        mappings = result['mappings']

        # Both should be strings in output
        assert isinstance(mappings[0]['value'], str)
        assert isinstance(mappings[1]['value'], str)

    def test_generate_value_mappings_class_method(self):
        """Test generating multiple value mappings."""
        items_with_enums = [
            {
                'name': 'ifOperStatus',
                'enum_data': {
                    'enums': [
                        {'value': '1', 'name': 'up'},
                        {'value': '2', 'name': 'down'}
                    ]
                }
            },
            {
                'name': 'ifAdminStatus',
                'enum_data': {
                    'enums': [
                        {'value': '1', 'name': 'up'},
                        {'value': '2', 'name': 'down'}
                    ]
                }
            }
        ]

        result = ValueMapping.generate_value_mappings(items_with_enums)

        assert len(result) == 2
        assert all(isinstance(vm, ValueMapping) for vm in result)
        names = [vm.name for vm in result]
        assert 'ifOperStatus' in names
        assert 'ifAdminStatus' in names

    def test_generate_value_mappings_skips_invalid(self):
        """Test that invalid entries are skipped."""
        items_with_enums = [
            {
                'name': 'valid',
                'enum_data': {
                    'enums': [{'value': '1', 'name': 'up'}]
                }
            },
            {
                'name': None,  # Invalid: no name
                'enum_data': {
                    'enums': [{'value': '1', 'name': 'up'}]
                }
            },
            {
                'name': 'noEnums',
                'enum_data': None  # Invalid: no enum data
            }
        ]

        result = ValueMapping.generate_value_mappings(items_with_enums)

        # Should only include the valid one
        assert len(result) == 1
        assert result[0].name == 'valid'

    def test_uuid_uniqueness(self):
        """Test that each value mapping gets unique UUID."""
        enums = [{'value': '1', 'name': 'test'}]
        vm1 = ValueMapping('test1', enums)
        vm2 = ValueMapping('test2', enums)

        assert vm1.uuid != vm2.uuid

    def test_complex_enum_names(self):
        """Test with complex enum names."""
        enums = [
            {'value': '1', 'name': 'operationallyUp'},
            {'value': '2', 'name': 'administrativelyDown'},
            {'value': '3', 'name': 'testing-phase-1'}
        ]
        vm = ValueMapping('complexStatus', enums)

        result = vm.generate_json_dict()
        mappings = result['mappings']

        # Enum names should be preserved exactly
        assert mappings[0]['newvalue'] == 'operationallyUp'
        assert mappings[1]['newvalue'] == 'administrativelyDown'
        assert mappings[2]['newvalue'] == 'testing-phase-1'
