"""Shared pytest fixtures for all tests."""
import pytest
from typing import Dict, List, Any


@pytest.fixture
def sample_mib_entry() -> Dict[str, Any]:
    """Sample MIB entry with all fields."""
    return {
        'MIB Module': 'IF-MIB',
        'OID': '.1.3.6.1.2.1.2.2.1.8',
        'Name': 'ifOperStatus',
        'Type': 'INTEGER',
        'Description': 'The current operational state of the interface.',
        'Syntax': 'INTEGER {up(1), down(2), testing(3), unknown(4), dormant(5), notPresent(6), lowerLayerDown(7)}'
    }


@pytest.fixture
def sample_mib_entry_no_syntax() -> Dict[str, Any]:
    """Sample MIB entry without Syntax field."""
    return {
        'MIB Module': 'CISCO-ENVMON-MIB',
        'OID': '.1.3.6.1.4.1.9.9.13.1.4.1.3',
        'Name': 'ciscoEnvMonFanState',
        'Type': 'INTEGER',
        'Description': '''The current state of the fan being instrumented.
normal(1) - fan is operating normally.
warning(2) - fan has a minor failure.
critical(3) - fan has a major failure.
shutdown(4) - fan has failed.
notPresent(5) - fan is not present.
notFunctioning(6) - fan is not functioning.'''
    }


@pytest.fixture
def sample_utilization_entry() -> Dict[str, Any]:
    """Sample utilization metric MIB entry."""
    return {
        'MIB Module': 'CISCO-PROCESS-MIB',
        'OID': '.1.3.6.1.4.1.9.9.109.1.1.1.1.5',
        'Name': 'cpmCPUTotal5sec',
        'Type': 'GAUGE32',
        'Description': 'The overall CPU busy percentage in the last 5 second period.'
    }


@pytest.fixture
def sample_temperature_entry() -> Dict[str, Any]:
    """Sample temperature metric MIB entry."""
    return {
        'MIB Module': 'CISCO-ENVMON-MIB',
        'OID': '.1.3.6.1.4.1.9.9.13.1.3.1.3',
        'Name': 'ciscoEnvMonTemperatureStatusValue',
        'Type': 'Integer32',
        'Description': 'The current measurement of the test point being instrumented.'
    }


@pytest.fixture
def sample_error_counter_entry() -> Dict[str, Any]:
    """Sample error counter MIB entry."""
    return {
        'MIB Module': 'IF-MIB',
        'OID': '.1.3.6.1.2.1.2.2.1.14',
        'Name': 'ifInErrors',
        'Type': 'Counter32',
        'Description': 'For packet-oriented interfaces, the number of inbound packets that contained errors.'
    }


@pytest.fixture
def sample_informational_entry() -> Dict[str, Any]:
    """Sample informational (non-alerting) MIB entry."""
    return {
        'MIB Module': 'IF-MIB',
        'OID': '.1.3.6.1.2.1.2.2.1.2',
        'Name': 'ifDescr',
        'Type': 'DISPLAYSTRING',
        'Description': 'A textual string containing information about the interface.'
    }


@pytest.fixture
def sample_discovery_table() -> List[Dict[str, Any]]:
    """Sample discovery rule table with multiple columns."""
    return [
        {
            'MIB Module': 'IF-MIB',
            'OID': '.1.3.6.1.2.1.2.2',
            'Name': 'ifTable',
            'Type': 'SEQUENCE OF',
            'Description': 'A list of interface entries.'
        },
        {
            'MIB Module': 'IF-MIB',
            'OID': '.1.3.6.1.2.1.2.2.1',
            'Name': 'ifEntry',
            'Type': 'IfEntry',
            'Description': 'An entry containing management information.'
        },
        {
            'MIB Module': 'IF-MIB',
            'OID': '.1.3.6.1.2.1.2.2.1.1',
            'Name': 'ifIndex',
            'Type': 'Integer32',
            'Description': 'A unique value, greater than zero, for each interface.'
        },
        {
            'MIB Module': 'IF-MIB',
            'OID': '.1.3.6.1.2.1.2.2.1.2',
            'Name': 'ifDescr',
            'Type': 'DISPLAYSTRING',
            'Description': 'A textual string containing information about the interface.'
        },
        {
            'MIB Module': 'IF-MIB',
            'OID': '.1.3.6.1.2.1.2.2.1.5',
            'Name': 'ifSpeed',
            'Type': 'Gauge32',
            'Description': 'An estimate of the interface current bandwidth.'
        },
        {
            'MIB Module': 'IF-MIB',
            'OID': '.1.3.6.1.2.1.2.2.1.8',
            'Name': 'ifOperStatus',
            'Type': 'INTEGER',
            'Syntax': 'INTEGER {up(1), down(2), testing(3)}',
            'Description': 'The current operational state of the interface.'
        }
    ]


@pytest.fixture
def sample_large_discovery_table() -> List[Dict[str, Any]]:
    """Sample discovery table with many columns requiring splitting."""
    base = [
        {
            'MIB Module': 'TEST-MIB',
            'OID': '.1.3.6.1.2.1.999.1',
            'Name': 'testTable',
            'Type': 'SEQUENCE OF',
            'Description': 'A test table.'
        },
        {
            'MIB Module': 'TEST-MIB',
            'OID': '.1.3.6.1.2.1.999.1.1',
            'Name': 'testEntry',
            'Type': 'TestEntry',
            'Description': 'A test entry.'
        },
        {
            'MIB Module': 'TEST-MIB',
            'OID': '.1.3.6.1.2.1.999.1.1.1',
            'Name': 'testIndex',
            'Type': 'Integer32',
            'Description': 'Index for test table.'
        }
    ]

    # Add 20 metric columns to force splitting
    for i in range(1, 21):
        base.append({
            'MIB Module': 'TEST-MIB',
            'OID': f'.1.3.6.1.2.1.999.1.1.{i+1}',
            'Name': f'testMetric{i}',
            'Type': 'Counter32',
            'Description': f'Test metric {i}.'
        })

    return base


@pytest.fixture
def template_info() -> Dict[str, Any]:
    """Sample template information."""
    return {
        'Group': 'Templates/Network devices',
        'Manufacturer': 'CISCO',
        'Model': 'Catalyst 9300',
        'Device': 'Switch',
        'Tags': 'network,switch,cisco',
        'Macros': '{$SNMP.TIMEOUT:5m},{$ICMP.TIMEOUT:30s}'
    }
