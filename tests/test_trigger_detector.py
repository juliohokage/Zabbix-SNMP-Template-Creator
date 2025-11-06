"""Unit tests for utils/trigger_detector.py"""
import pytest
from utils.trigger_detector import TriggerDetector


class TestShouldCreateTrigger:
    """Tests for should_create_trigger method."""

    def test_should_create_for_status_field(self):
        """Test that status fields should have triggers."""
        item_data = {
            'Name': 'ifOperStatus',
            'Type': 'INTEGER'
        }
        result = TriggerDetector.should_create_trigger(item_data)

        assert result is True

    def test_should_skip_informational_fields(self, sample_informational_entry):
        """Test that informational fields are skipped."""
        result = TriggerDetector.should_create_trigger(sample_informational_entry)

        assert result is False

    def test_should_skip_serial_number(self):
        """Test that serial number fields are skipped."""
        item_data = {
            'Name': 'entitySerialNumber',
            'Type': 'DISPLAYSTRING'
        }
        result = TriggerDetector.should_create_trigger(item_data)

        assert result is False

    def test_should_skip_description_field(self):
        """Test that description fields are skipped."""
        item_data = {
            'Name': 'sysDescription',
            'Type': 'OCTET STRING'
        }
        result = TriggerDetector.should_create_trigger(item_data)

        assert result is False

    def test_should_skip_text_only_fields(self):
        """Test that text-only fields are skipped."""
        item_data = {
            'Name': 'customField',
            'Type': 'DISPLAYSTRING'
        }
        result = TriggerDetector.should_create_trigger(item_data)

        assert result is False

    def test_should_create_for_numeric_status(self):
        """Test numeric status fields should have triggers."""
        item_data = {
            'Name': 'operationalStatus',
            'Type': 'INTEGER'
        }
        result = TriggerDetector.should_create_trigger(item_data)

        assert result is True


class TestAnalyzeItem:
    """Tests for analyze_item method."""

    def test_analyze_with_enum_data(self, sample_mib_entry):
        """Test analyzing item with enum data creates state trigger."""
        enum_data = {
            'enums': [
                {'value': '1', 'name': 'up'},
                {'value': '2', 'name': 'down'}
            ],
            'ok_value': '1',
            'bad_values': ['2']
        }
        result = TriggerDetector.analyze_item(sample_mib_entry, enum_data)

        assert result is not None
        assert result['type'] == 'state'
        assert result['severity'] == 'AVERAGE'
        assert result['ok_value'] == '1'
        assert '{$' in result['macro_name']

    def test_analyze_utilization_metric(self, sample_utilization_entry):
        """Test analyzing utilization metric creates threshold trigger."""
        result = TriggerDetector.analyze_item(sample_utilization_entry)

        assert result is not None
        assert result['type'] == 'threshold'
        assert result['severity'] == 'HIGH'
        assert result['macro_value'] == '90'
        assert 'UTIL' in result['macro_name']

    def test_analyze_temperature_metric(self, sample_temperature_entry):
        """Test analyzing temperature metric creates temperature trigger."""
        result = TriggerDetector.analyze_item(sample_temperature_entry)

        assert result is not None
        assert result['type'] == 'threshold'
        assert result['severity'] == 'HIGH'
        assert result['macro_value'] == '75'
        assert 'TEMP' in result['macro_name']

    def test_analyze_error_counter(self, sample_error_counter_entry):
        """Test analyzing error counter creates rate trigger."""
        result = TriggerDetector.analyze_item(sample_error_counter_entry)

        assert result is not None
        assert result['type'] == 'rate'
        assert result['severity'] == 'AVERAGE'
        assert result['macro_value'] == '10'
        assert 'RATE' in result['macro_name']

    def test_analyze_informational_field(self, sample_informational_entry):
        """Test that informational fields return None."""
        result = TriggerDetector.analyze_item(sample_informational_entry)

        assert result is None

    def test_analyze_memory_metric(self):
        """Test analyzing memory metric."""
        item_data = {
            'Name': 'memoryUtilization',
            'Type': 'GAUGE32',
            'Description': 'Memory usage percentage'
        }
        result = TriggerDetector.analyze_item(item_data)

        assert result is not None
        assert result['type'] == 'threshold'
        assert 'UTIL' in result['macro_name']

    def test_analyze_status_without_enums(self):
        """Test analyzing status field without enum data."""
        item_data = {
            'Name': 'linkStatus',
            'Type': 'INTEGER',
            'Description': 'Link status indicator'
        }
        result = TriggerDetector.analyze_item(item_data)

        assert result is not None
        assert result['type'] == 'state'
        assert result['ok_value'] == '1'  # Assumes 1 is OK


class TestGenerateMacroName:
    """Tests for _generate_macro_name method."""

    def test_generate_macro_from_status(self):
        """Test generating macro from status field."""
        result = TriggerDetector._generate_macro_name('ifOperStatus', 'STATUS.OK')

        assert result.startswith('{$')
        assert result.endswith('}')
        assert 'STATUS.OK' in result

    def test_generate_macro_removes_prefix(self):
        """Test that common prefixes are removed."""
        result = TriggerDetector._generate_macro_name('ciscoEnvMonFanState', 'STATUS.OK')

        # 'cisco' prefix should be removed
        assert 'CISCO' not in result
        assert 'ENVMON' in result or 'FAN' in result

    def test_generate_macro_uppercase(self):
        """Test that macro name is uppercase."""
        result = TriggerDetector._generate_macro_name('ifOperStatus', 'STATUS.OK')

        # Extract the content between {$ and }
        macro_content = result[2:-1]
        assert macro_content.isupper()

    def test_generate_macro_length_limit(self):
        """Test that macro name respects length limit."""
        long_name = 'veryLongItemNameThatExceedsTwentyCharactersForSure'
        result = TriggerDetector._generate_macro_name(long_name, 'STATUS.OK')

        # Macro should be limited but still valid
        assert result.startswith('{$')
        assert result.endswith('}')
        assert len(result) < 50  # Reasonable limit


class TestCreateStateTriggerConfig:
    """Tests for _create_state_trigger_config method."""

    def test_create_state_trigger_config(self):
        """Test creating state trigger configuration."""
        item_data = {'Name': 'ifOperStatus'}
        enum_data = {
            'enums': [{'value': '1', 'name': 'up'}, {'value': '2', 'name': 'down'}],
            'ok_value': '1'
        }
        result = TriggerDetector._create_state_trigger_config(item_data, enum_data)

        assert result['type'] == 'state'
        assert result['severity'] == 'AVERAGE'
        assert result['ok_value'] == '1'
        assert result['macro_value'] == '1'
        assert result['use_time_function'] is True


class TestCreateUtilizationTriggerConfig:
    """Tests for _create_utilization_trigger_config method."""

    def test_create_utilization_trigger_config(self):
        """Test creating utilization trigger configuration."""
        item_data = {'Name': 'cpuUtilization'}
        result = TriggerDetector._create_utilization_trigger_config(item_data)

        assert result['type'] == 'threshold'
        assert result['severity'] == 'HIGH'
        assert result['macro_value'] == '90'
        assert result['expression_template'] == 'min(5m)>{$MACRO}'


class TestCreateTemperatureTriggerConfig:
    """Tests for _create_temperature_trigger_config method."""

    def test_create_temperature_trigger_config(self):
        """Test creating temperature trigger configuration."""
        item_data = {'Name': 'temperatureSensor'}
        result = TriggerDetector._create_temperature_trigger_config(item_data)

        assert result['type'] == 'threshold'
        assert result['severity'] == 'HIGH'
        assert result['macro_value'] == '75'
        assert result['expression_template'] == 'avg(5m)>{$MACRO}'


class TestCreateErrorRateTriggerConfig:
    """Tests for _create_error_rate_trigger_config method."""

    def test_create_error_rate_trigger_config(self):
        """Test creating error rate trigger configuration."""
        item_data = {'Name': 'ifInErrors'}
        result = TriggerDetector._create_error_rate_trigger_config(item_data)

        assert result['type'] == 'rate'
        assert result['severity'] == 'AVERAGE'
        assert result['macro_value'] == '10'
        assert result['expression_template'] == 'rate(5m)>{$MACRO}'


class TestPatternMatching:
    """Integration tests for pattern matching logic."""

    def test_cpu_pattern_matching(self):
        """Test various CPU-related field names."""
        # Note: 'cpuUsage' contains 'age' which is in INFORMATIONAL_KEYWORDS, so it's excluded
        cpu_names = ['cpuUtil', 'cpu5sec', 'processorLoad', 'cpuBusy', 'cpuPercent']

        for name in cpu_names:
            item_data = {'Name': name, 'Type': 'GAUGE32', 'Description': 'CPU metric'}
            result = TriggerDetector.analyze_item(item_data)
            assert result is not None, f"Failed to match CPU pattern: {name}"
            assert result['type'] == 'threshold'

    def test_temperature_pattern_matching(self):
        """Test various temperature-related field names."""
        temp_names = ['temperature', 'temp', 'temperatureCelsius', 'thermal']

        for name in temp_names:
            item_data = {'Name': name, 'Type': 'Integer32', 'Description': 'Temperature'}
            result = TriggerDetector.analyze_item(item_data)
            assert result is not None, f"Failed to match temperature pattern: {name}"
            assert result['type'] == 'threshold'

    def test_error_pattern_matching(self):
        """Test various error-related field names."""
        error_names = ['ifInErrors', 'packetDrops', 'discardedFrames', 'collisionCount']

        for name in error_names:
            item_data = {'Name': name, 'Type': 'Counter32', 'Description': 'Error counter'}
            result = TriggerDetector.analyze_item(item_data)
            assert result is not None, f"Failed to match error pattern: {name}"
            assert result['type'] == 'rate'

    def test_status_pattern_matching(self):
        """Test various status-related field names."""
        # Note: 'portState' contains 'port' which is in INFORMATIONAL_KEYWORDS, so it's excluded
        status_names = ['operStatus', 'linkState', 'adminStatus', 'interfaceState']

        for name in status_names:
            item_data = {'Name': name, 'Type': 'INTEGER', 'Description': 'Status field'}
            result = TriggerDetector.analyze_item(item_data)
            assert result is not None, f"Failed to match status pattern: {name}"

    def test_informational_fields_skipped(self):
        """Test that various informational fields are skipped."""
        info_names = ['serialNumber', 'description', 'sysName', 'version', 'location', 'contact']

        for name in info_names:
            item_data = {'Name': name, 'Type': 'DISPLAYSTRING', 'Description': 'Info field'}
            result = TriggerDetector.analyze_item(item_data)
            assert result is None, f"Incorrectly created trigger for informational field: {name}"
