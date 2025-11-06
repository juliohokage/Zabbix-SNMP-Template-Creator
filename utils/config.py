from types import SimpleNamespace

# Constants
MAX_KEY_LENGTH = 255
MAX_SNMP_OID_LENGTH = 250
MAX_OIDS_PER_WALK = 8  # Maximum OIDs per walk item (conservative, leaves buffer)
MAX_INDEX_OIDS = 3  # Maximum number of index OIDs to include in each walk
MIN_INDEX_SCORE = 2  # Minimum score to be considered an index

SNMP_ITEM=SimpleNamespace(
    HISTORY="90d",
    TRENDS="365d",
    DELAY="1h",
    TYPE="SNMP_AGENT"
)

SNMP_TRAP=SimpleNamespace(
    HISTORY="90d",
    DELAY="0m",
    TRENDS="0",
    TRIGGER=SimpleNamespace(
        PRIORITY="INFO",
        TYPE="MULTIPLE",
        CLOSE="YES"
    ),
    TYPE="SNMP_TRAP",
    VALUE_TYPE="LOG"
)

SNMP_WALK_ITEM=SimpleNamespace(
    HISTORY="0d",
    TRENDS="0",
    DELAY="1m",
    TYPE="SNMP_AGENT",
    VALUE_TYPE= 'TEXT'
)

ITEM_PROTOTYPE=SimpleNamespace(
    HISTORY="90d",
    TRENDS="365d",
    DELAY="1h",
    TYPE="DEPENDENT",
    VALUE_TYPE= 'TEXT'
)

DISCOVERY_RULE=SimpleNamespace(
    TYPE="DEPENDENT"
)

TRIGGER=SimpleNamespace(
    ENABLED=True,  # Auto-generate triggers by default
    MANUAL_CLOSE=False,
    DEFAULT_SEVERITY="AVERAGE"
)