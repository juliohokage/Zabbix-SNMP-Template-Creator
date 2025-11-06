"""Unit tests for utils/index_detector.py"""
import pytest
from utils.index_detector import detect_index_oids, generate_lld_macro_name, create_lld_macros
from utils.config import MIN_INDEX_SCORE, MAX_INDEX_OIDS


class TestDetectIndexOids:
    """Tests for detect_index_oids function."""

    def test_detect_index_by_name(self, sample_discovery_table):
        """Test detecting index OID by name keyword."""
        # ifTable: ifIndex should be detected as index
        result = detect_index_oids(sample_discovery_table)

        assert len(result) > 0
        index_names = [entry['Name'] for entry in result]
        assert 'ifIndex' in index_names

    def test_detect_descr_as_index(self, sample_discovery_table):
        """Test that description fields can be detected as index."""
        result = detect_index_oids(sample_discovery_table)

        index_names = [entry['Name'] for entry in result]
        # ifDescr should be detected (has 'descr' keyword)
        assert 'ifDescr' in index_names

    def test_position_bias(self):
        """Test that earlier columns get position bias."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'column1', 'Type': 'INTEGER', 'OID': '.1.1'},
            {'Name': 'column2', 'Type': 'INTEGER', 'OID': '.1.2'},
            {'Name': 'column3', 'Type': 'INTEGER', 'OID': '.1.3'}
        ]

        result = detect_index_oids(table)

        # First columns should be preferred (position bias)
        assert len(result) > 0
        assert result[0]['Name'] == 'column1'

    def test_type_scoring_integer(self):
        """Test that INTEGER types get appropriate score."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'indexField', 'Type': 'INTEGER', 'OID': '.1.1'},
            {'Name': 'dataField', 'Type': 'DISPLAYSTRING', 'OID': '.1.2'}
        ]

        result = detect_index_oids(table)

        # indexField should score higher due to INTEGER type + name
        index_names = [entry['Name'] for entry in result]
        assert 'indexField' in index_names

    def test_type_scoring_displaystring(self):
        """Test that DISPLAYSTRING types for descriptive fields score well."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'descr', 'Type': 'DISPLAYSTRING', 'OID': '.1.1'},
            {'Name': 'value', 'Type': 'Counter32', 'OID': '.1.2'}
        ]

        result = detect_index_oids(table)

        # 'descr' should be detected as index (name + type bonus)
        index_names = [entry['Name'] for entry in result]
        assert 'descr' in index_names

    def test_max_indices_limit(self):
        """Test that maximum number of indices is respected."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'index1', 'Type': 'INTEGER', 'OID': '.1.1'},
            {'Name': 'index2', 'Type': 'INTEGER', 'OID': '.1.2'},
            {'Name': 'index3', 'Type': 'INTEGER', 'OID': '.1.3'},
            {'Name': 'index4', 'Type': 'INTEGER', 'OID': '.1.4'},
            {'Name': 'metric1', 'Type': 'Counter32', 'OID': '.1.5'}
        ]

        result = detect_index_oids(table, max_indices=MAX_INDEX_OIDS)

        # Should respect MAX_INDEX_OIDS limit
        assert len(result) <= MAX_INDEX_OIDS

    def test_minimum_score_threshold(self):
        """Test that only OIDs meeting minimum score are included."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'goodIndex', 'Type': 'INTEGER', 'OID': '.1.1'},  # High score
            {'Name': 'randomField', 'Type': 'Counter32', 'OID': '.1.2'}  # Low score
        ]

        result = detect_index_oids(table)

        # Only high-scoring OIDs should be included
        assert len(result) >= 1
        assert result[0]['Name'] == 'goodIndex'

    def test_ensure_at_least_one_index(self):
        """Test that at least one index is always returned."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'metric1', 'Type': 'Counter32', 'OID': '.1.1'},
            {'Name': 'metric2', 'Type': 'Gauge32', 'OID': '.1.2'}
        ]

        result = detect_index_oids(table)

        # Should return at least 1 even if scores are low
        assert len(result) >= 1

    def test_complex_scoring_scenario(self):
        """Test complex scenario with mixed signal strengths."""
        table = [
            {'Name': 'testTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'testEntry', 'Type': 'TestEntry'},
            {'Name': 'ifIndex', 'Type': 'Integer32', 'OID': '.1.1'},  # Strong: name+type+position
            {'Name': 'ifDescr', 'Type': 'DISPLAYSTRING', 'OID': '.1.2'},  # Strong: name+type
            {'Name': 'ifSpeed', 'Type': 'Gauge32', 'OID': '.1.3'},  # Weak: metric-like
            {'Name': 'ifErrors', 'Type': 'Counter32', 'OID': '.1.4'}  # Weak: clearly metric
        ]

        result = detect_index_oids(table)

        index_names = [entry['Name'] for entry in result]
        # Should include ifIndex and ifDescr, not ifSpeed or ifErrors
        assert 'ifIndex' in index_names
        assert 'ifDescr' in index_names
        assert 'ifErrors' not in index_names


class TestGenerateLldMacroName:
    """Tests for generate_lld_macro_name function."""

    def test_generate_basic_macro(self):
        """Test generating LLD macro from simple name."""
        result = generate_lld_macro_name('ifIndex')

        # 'if' prefix is removed, so ifIndex becomes {#INDEX}
        assert result == '{#INDEX}'

    def test_generate_macro_removes_prefix(self):
        """Test that common prefixes are removed."""
        result = generate_lld_macro_name('ospfv3IfIndex')

        assert result == '{#IFINDEX}'
        assert 'OSPFV3' not in result

    def test_generate_macro_cisco_prefix(self):
        """Test removing cisco prefix."""
        result = generate_lld_macro_name('ciscoEnvMonFanIndex')

        assert result == '{#ENVMONFANINDEX}'
        assert 'CISCO' not in result

    def test_generate_macro_if_prefix(self):
        """Test removing 'if' prefix."""
        result = generate_lld_macro_name('ifDescr')

        assert result == '{#DESCR}'

    def test_generate_macro_ent_prefix(self):
        """Test removing 'ent' prefix."""
        result = generate_lld_macro_name('entPhysicalIndex')

        assert result == '{#PHYSICALINDEX}'

    def test_generate_macro_uppercase(self):
        """Test that macro is uppercase."""
        result = generate_lld_macro_name('mixedCaseFieldName')

        assert result.isupper()
        assert result.startswith('{#')
        assert result.endswith('}')

    def test_generate_macro_preserves_meaning(self):
        """Test that macro name is meaningful."""
        result = generate_lld_macro_name('sensorThresholdIndex')

        # Should contain key parts of the name
        assert '{#' in result
        assert '}' in result
        # Content should be related to original name
        macro_content = result[2:-1]
        assert len(macro_content) > 0


class TestCreateLldMacros:
    """Tests for create_lld_macros function."""

    def test_create_macros_basic(self):
        """Test creating LLD macros from index OIDs."""
        index_oids = [
            {'Name': 'ifIndex', 'OID': '.1.3.6.1.2.1.2.2.1.1'},
            {'Name': 'ifDescr', 'OID': '.1.3.6.1.2.1.2.2.1.2'}
        ]

        result = create_lld_macros(index_oids)

        assert len(result) == 2
        # 'if' prefix is removed from both
        assert result[0]['lld_macro'] == '{#INDEX}'
        assert result[1]['lld_macro'] == '{#DESCR}'

    def test_create_macros_paths(self):
        """Test that paths are correctly formatted."""
        index_oids = [
            {'Name': 'ifIndex', 'OID': '.1.3.6.1.2.1.2.2.1.1'}
        ]

        result = create_lld_macros(index_oids)

        assert len(result) == 1
        # Path should use $[{#SNMPINDEX}] and last OID segment
        assert '$[{#SNMPINDEX}]' in result[0]['path']
        assert '.1' in result[0]['path']

    def test_create_macros_multiple_indices(self):
        """Test creating macros for multiple indices."""
        index_oids = [
            {'Name': 'index1', 'OID': '.1.1.1.1'},
            {'Name': 'index2', 'OID': '.1.1.1.2'},
            {'Name': 'descr', 'OID': '.1.1.1.3'}
        ]

        result = create_lld_macros(index_oids)

        assert len(result) == 3
        # Each should have unique macro and path
        macros = [m['lld_macro'] for m in result]
        assert len(set(macros)) == 3  # All unique

    def test_create_macros_empty_list(self):
        """Test creating macros from empty list."""
        result = create_lld_macros([])

        assert result == []

    def test_create_macros_path_format(self):
        """Test that path format is correct for Zabbix."""
        index_oids = [
            {'Name': 'testIndex', 'OID': '.1.2.3.4.5'}
        ]

        result = create_lld_macros(index_oids)

        # Path should be: $[{#SNMPINDEX}].5
        assert result[0]['path'] == '$[{#SNMPINDEX}].5'


class TestHybridScoringIntegration:
    """Integration tests for the hybrid scoring system."""

    def test_realistic_interface_table(self):
        """Test with realistic ifTable structure."""
        table = [
            {'Name': 'ifTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'ifEntry', 'Type': 'IfEntry'},
            {'Name': 'ifIndex', 'Type': 'InterfaceIndex', 'OID': '.1'},
            {'Name': 'ifDescr', 'Type': 'DISPLAYSTRING', 'OID': '.2'},
            {'Name': 'ifType', 'Type': 'INTEGER', 'OID': '.3'},
            {'Name': 'ifMtu', 'Type': 'Integer32', 'OID': '.4'},
            {'Name': 'ifSpeed', 'Type': 'Gauge32', 'OID': '.5'},
            {'Name': 'ifInOctets', 'Type': 'Counter32', 'OID': '.10'},
            {'Name': 'ifOutOctets', 'Type': 'Counter32', 'OID': '.16'}
        ]

        result = detect_index_oids(table)

        index_names = [entry['Name'] for entry in result]
        # Should detect ifIndex and ifDescr as indices
        assert 'ifIndex' in index_names
        assert 'ifDescr' in index_names
        # Should NOT detect counters
        assert 'ifInOctets' not in index_names
        assert 'ifOutOctets' not in index_names

    def test_realistic_sensor_table(self):
        """Test with realistic sensor table structure."""
        table = [
            {'Name': 'entSensorTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'entSensorEntry', 'Type': 'EntSensorEntry'},
            {'Name': 'entSensorIndex', 'Type': 'Integer32', 'OID': '.1'},
            {'Name': 'entSensorType', 'Type': 'INTEGER', 'OID': '.2'},
            {'Name': 'entSensorValue', 'Type': 'Integer32', 'OID': '.4'},
            {'Name': 'entSensorStatus', 'Type': 'INTEGER', 'OID': '.5'}
        ]

        result = detect_index_oids(table)

        index_names = [entry['Name'] for entry in result]
        # Should detect index and type as indices
        assert 'entSensorIndex' in index_names
        # Value and Status are metrics, not indices
        assert len([n for n in index_names if 'Value' in n or 'Status' in n]) <= 1

    def test_edge_case_all_metrics(self):
        """Test edge case where all fields look like metrics."""
        table = [
            {'Name': 'metricsTable', 'Type': 'SEQUENCE OF'},
            {'Name': 'metricsEntry', 'Type': 'MetricsEntry'},
            {'Name': 'metric1', 'Type': 'Counter64', 'OID': '.1'},
            {'Name': 'metric2', 'Type': 'Counter64', 'OID': '.2'},
            {'Name': 'metric3', 'Type': 'Counter64', 'OID': '.3'}
        ]

        result = detect_index_oids(table)

        # Should still return at least one index (first column by position)
        assert len(result) >= 1
        assert result[0]['Name'] == 'metric1'
