"""
Index OID detection utility using hybrid scoring system.

This module provides intelligent detection of index/identifier OIDs in SNMP tables
to support proper LLD (Low-Level Discovery) macro generation.
"""

from typing import List, Dict, Any
from utils.config import MAX_INDEX_OIDS, MIN_INDEX_SCORE
from utils.logger import logger


def detect_index_oids(discovery_table: List[Dict[str, Any]], max_indices: int = MAX_INDEX_OIDS) -> List[Dict[str, Any]]:
    """
    Detect index OIDs using hybrid scoring system.

    Analyzes OID names, types, and positions to identify which OIDs are
    indices/identifiers (like ifIndex, ifDescr) vs metrics (like ifSpeed, ifInOctets).

    Args:
        discovery_table: List of OID dictionaries from MIB data
        max_indices: Maximum number of index OIDs to return

    Returns:
        List of index OID dictionaries, sorted by original position

    Examples:
        >>> table = [
        ...     {'Name': 'ifTable', 'Type': 'SEQUENCE OF'},
        ...     {'Name': 'ifEntry', 'Type': 'IfEntry'},
        ...     {'Name': 'ifIndex', 'Type': 'INTEGER'},       # Index
        ...     {'Name': 'ifDescr', 'Type': 'DISPLAYSTRING'}, # Name/Description
        ...     {'Name': 'ifSpeed', 'Type': 'GAUGE32'},       # Metric
        ... ]
        >>> indices = detect_index_oids(table)
        >>> [idx['Name'] for idx in indices]
        ['ifIndex', 'ifDescr']
    """
    # Skip Table[0] and Entry[1], analyze columns[2+]
    columns = discovery_table[2:]
    if not columns:
        logger.warning("No columns found in discovery table after Table and Entry")
        return []

    scored_columns = []

    for position, entry in enumerate(columns):
        score = 0
        name_lower = entry.get('Name', '').lower()
        entry_type = entry.get('Type', '')

        # Signal 1: Name contains index keywords
        index_keywords = ['index', 'idx', 'id', 'key', 'number']
        if any(kw in name_lower for kw in index_keywords):
            score += 3
            logger.debug(f"  {entry['Name']}: +3 for index keyword")

        # Signal 2: Name contains descriptive keywords
        name_keywords = ['descr', 'name', 'label', 'text']
        if any(kw in name_lower for kw in name_keywords):
            score += 2
            logger.debug(f"  {entry['Name']}: +2 for name keyword")

        # Signal 3: Type suggests index (integer types)
        integer_types = ['INTEGER', 'Unsigned32', 'GAUGE32', 'Integer32', 'InterfaceIndex', 'COUNTER32']
        if entry_type in integer_types:
            score += 1
            logger.debug(f"  {entry['Name']}: +1 for integer type")

        # Signal 4: Type suggests name (string types)
        string_types = ['DISPLAYSTRING', 'OCTET STRING', 'SnmpAdminString']
        if entry_type in string_types:
            score += 2
            logger.debug(f"  {entry['Name']}: +2 for string type")

        # Signal 5: Position bias (earlier = more likely index)
        if position < 3:
            position_bonus = 3 - position  # pos 0=+3, pos 1=+2, pos 2=+1
            score += position_bonus
            logger.debug(f"  {entry['Name']}: +{position_bonus} for early position")

        logger.debug(f"  {entry['Name']}: Total score = {score}")
        scored_columns.append((score, position, entry))

    # Sort by score (desc), then by position (asc) for ties
    scored_columns.sort(key=lambda x: (-x[0], x[1]))

    # Take top N with score above threshold, but ensure at least 1
    high_scorers = [s for s in scored_columns if s[0] >= MIN_INDEX_SCORE]
    num_indices = min(max(1, len(high_scorers)), max_indices)

    logger.info(f"Detected {num_indices} index OIDs from {len(columns)} columns")

    # Re-sort selected indices by original position to maintain order
    selected = sorted(scored_columns[:num_indices], key=lambda x: x[1])

    indices = [entry for _, _, entry in selected]
    logger.info(f"Index OIDs: {[idx['Name'] for idx in indices]}")

    return indices


def generate_lld_macro_name(oid_name: str) -> str:
    """
    Generate LLD macro name from OID name.

    Converts OID name to Zabbix LLD macro format: {#MACRONAME}

    Examples:
        >>> generate_lld_macro_name('ifIndex')
        '{#IFINDEX}'
        >>> generate_lld_macro_name('ospfv3IfIndex')
        '{#OSPFV3IFINDEX}'
        >>> generate_lld_macro_name('entPhysicalDescr')
        '{#ENTPHYSICALDESCR}'

    Args:
        oid_name: Original OID name from MIB

    Returns:
        LLD macro name in format {#MACRONAME}
    """
    # Remove common prefixes to shorten macro names
    name = oid_name
    for prefix in ['ospfv3', 'ent', 'if', 'cisco']:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break

    # Convert to uppercase and wrap in {# }
    macro_name = f"{{#{name.upper()}}}"

    return macro_name


def create_lld_macros(index_oids: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Create LLD macro definitions from index OIDs.

    Args:
        index_oids: List of index OID dictionaries

    Returns:
        List of LLD macro dictionaries with 'lld_macro' and 'oid' keys

    Example:
        >>> indices = [
        ...     {'Name': 'ifIndex', 'OID': '.1.3.6.1.2.1.2.2.1.1'},
        ...     {'Name': 'ifDescr', 'OID': '.1.3.6.1.2.1.2.2.1.2'}
        ... ]
        >>> macros = create_lld_macros(indices)
        >>> macros
        [
            {'lld_macro': '{#IFINDEX}', 'path': '$[{#SNMPINDEX}].1'},
            {'lld_macro': '{#IFDESCR}', 'path': '$[{#SNMPINDEX}].2'}
        ]
    """
    lld_macros = []
    seen_macros = set()

    for idx_oid in index_oids:
        macro_name = generate_lld_macro_name(idx_oid['Name'])

        # Skip if we've already added this macro name
        if macro_name in seen_macros:
            logger.debug(f"Skipping duplicate LLD macro: {macro_name} for OID {idx_oid['Name']}")
            continue

        # Extract last part of OID for path
        oid_suffix = idx_oid['OID'].split('.')[-1]

        lld_macros.append({
            'lld_macro': macro_name,
            'path': f"$[{{#SNMPINDEX}}].{oid_suffix}"
        })
        seen_macros.add(macro_name)

    logger.debug(f"Created LLD macros: {[m['lld_macro'] for m in lld_macros]}")

    return lld_macros
