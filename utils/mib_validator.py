import pandas as pd
from collections import defaultdict
from typing import List, Dict, Tuple, Any
from utils.logger import logger
from utils.index_detector import detect_index_oids
from utils.config import MAX_OIDS_PER_WALK

class UnmatchedDataError(Exception):
    """Raised when there is unmatched data after validation."""
    pass

class MIBValidator:
    """
    A class for validating and extracting data from Excel files containing MIB information.
    """

    @classmethod
    def extract_from_excel(cls, excel_file: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        """
        Extract and validate data from an Excel file.
        This is a factory method that separates the creation of the Template object from its source.
        Here we parse the necessary data from Excel. Later, we could do so from a json object, a database, etc.

        Args:
            excel_file (str): Path to the Excel file.

        Returns:
            Tuple containing:
            - List of preprocessed SNMP items
            - List of preprocessed SNMP traps
            - Template information dictionary
            - Dictionary of discovery rule tables

        Raises:
            FileNotFoundError: If the Excel file doesn't exist.
            ValueError: If required sheets are missing or malformed.
            Exception: For other pandas/Excel reading errors.
        """
        try:
            excel_data = pd.ExcelFile(excel_file)
        except FileNotFoundError:
            logger.error(f"Excel file not found: {excel_file}")
            raise
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise ValueError(f"Failed to read Excel file '{excel_file}': {e}")

        all_sheets_data = {}

        na_values = ['nan', 'NaN', 'N/A', '']

        try:
            for sheet_name in excel_data.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, na_values=na_values)
                df = df.where(pd.notnull(df), None)
                sheet_data = df.to_dict('records')
                all_sheets_data[sheet_name] = sheet_data
        except Exception as e:
            logger.error(f"Error processing sheet '{sheet_name}': {e}")
            raise ValueError(f"Failed to process Excel sheet '{sheet_name}': {e}")
        
        # Validate required sheets exist
        required_sheets = ["SNMP Items", "SNMP Traps", "Template Information"]
        missing_sheets = [sheet for sheet in required_sheets if sheet not in all_sheets_data]

        if missing_sheets:
            logger.error(f"Missing required sheets: {', '.join(missing_sheets)}")
            raise ValueError(f"Excel file is missing required sheets: {', '.join(missing_sheets)}")

        snmp_items_json_list = all_sheets_data.get("SNMP Items", [])
        snmp_traps_json_list = all_sheets_data.get("SNMP Traps", [])
        template_info = all_sheets_data.get("Template Information", [])
        template_info_json = template_info[0] if template_info else {}

        mib_sheet_name = next((sheet for sheet in all_sheets_data.keys() if "MIB" in sheet), None)
        if not mib_sheet_name:
            logger.error("No MIB Data sheet found in Excel file")
            raise ValueError("Excel file must contain a sheet with 'MIB' in its name")

        mib_data_json_list = all_sheets_data.get(mib_sheet_name, [])

        preprocessed_snmp_items = cls._preprocess_and_validate(snmp_items_json_list, mib_data_json_list, "SNMP Items")
        preprocessed_snmp_traps = cls._preprocess_and_validate(snmp_traps_json_list, mib_data_json_list, "SNMP Traps")
        discovery_rule_tables = cls._collect_discovery_rule_tables(mib_data_json_list)

        return preprocessed_snmp_items, preprocessed_snmp_traps, template_info_json, discovery_rule_tables

    @classmethod
    def _preprocess_and_validate(cls, input_data: List[Dict[str, Any]], mib_data: List[Dict[str, Any]], entity_type: str) -> List[Dict[str, Any]]:
        """
        Preprocess and validate input data against MIB data.

        Args:
            input_data (List[Dict[str, Any]]): List of input data dictionaries.
            mib_data (List[Dict[str, Any]]): List of MIB data dictionaries.
            entity_type (str): Type of entity being validated (e.g., "SNMP Items", "SNMP Traps").

        Returns:
            List[Dict[str, Any]]: List of validated and preprocessed data.

        Raises:
            UnmatchedDataError: If there are unmatched entries after validation.
        """
        oid_dict, name_dict, null_entries = cls._preprocess_input_data(input_data)
        mib_oid_dict, mib_name_dict = cls._create_mib_dictionaries(mib_data)
        matched_data, unmatched_data = cls._match_entries(input_data, mib_oid_dict, mib_name_dict)

        cls._print_results(matched_data, unmatched_data, null_entries, entity_type)

        if unmatched_data:
            raise UnmatchedDataError(f"Validation failed: {len(unmatched_data)} unmatched entries found for {entity_type}.\n\t{unmatched_data}\nCheck source document for invalid entries.")

        return matched_data

    @staticmethod
    def _preprocess_input_data(input_data):
        """
        Preprocess input data to handle duplicates and null entries.

        Args:
            input_data (List[Dict[str, Any]]): List of input data dictionaries.

        Returns:
            Tuple containing:
            - Dictionary of entries keyed by OID
            - Dictionary of entries keyed by Name
            - List of null entries
        """
        oid_count = defaultdict(list)
        name_count = defaultdict(list)
        oid_dict = {}
        name_dict = {}
        null_entries = []
        
        # First pass: count occurrences and store indices
        for index, entry in enumerate(input_data):
            oid, name = entry.get('OID'), entry.get('Name')
            if oid:
                oid_count[oid].append(index)
            if name:
                name_count[name].append(index)
        
        # Second pass: categorize entries and handle duplicates
        for index, entry in enumerate(input_data):
            oid, name = entry.get('OID'), entry.get('Name')
            
            if not oid and not name:
                null_entries.append(entry)
                continue

            entry_copy = entry.copy()

            if oid and len(oid_count[oid]) > 1:
                for dup_index in oid_count[oid]:
                    input_data[dup_index]['OID'] = None
                entry_copy['OID'] = None

            if name and len(name_count[name]) > 1:
                for dup_index in name_count[name]:
                    input_data[dup_index]['Name'] = None
                entry_copy['Name'] = None

            if entry_copy['OID']:
                oid_dict[oid] = entry_copy
            if entry_copy['Name']:
                name_dict[name] = entry_copy

        return oid_dict, name_dict, null_entries

    @staticmethod
    def _create_mib_dictionaries(mib_data: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        Create dictionaries of MIB data keyed by OID and Name.

        Args:
            mib_data (List[Dict[str, Any]]): List of MIB data dictionaries.

        Returns:
            Tuple containing:
            - Dictionary of MIB entries keyed by OID
            - Dictionary of MIB entries keyed by Name
        """
        mib_oid_dict = {entry['OID']: entry for entry in mib_data if 'OID' in entry}
        mib_name_dict = {entry['Name']: entry for entry in mib_data if 'Name' in entry}
        return mib_oid_dict, mib_name_dict

    @staticmethod
    def _match_entries(input_data: List[Dict[str, Any]], mib_oid_dict: Dict[str, Dict[str, Any]], mib_name_dict: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Match input entries against MIB data.

        Args:
            input_data (List[Dict[str, Any]]): List of input data dictionaries.
            mib_oid_dict (Dict[str, Dict[str, Any]]): Dictionary of MIB entries keyed by OID.
            mib_name_dict (Dict[str, Dict[str, Any]]): Dictionary of MIB entries keyed by Name.

        Returns:
            Tuple containing:
            - List of matched entries
            - List of unmatched entries
        """
        matched_data = []
        unmatched_data = []

        for entry in input_data:
            oid, name = entry.get('OID'), entry.get('Name')
            
            if not oid and not name:
                unmatched_data.append(entry)
                continue

            matched = False

            if oid and oid in mib_oid_dict:
                matched_data.append(mib_oid_dict[oid])
                matched = True
            elif name and name in mib_name_dict:
                matched_data.append(mib_name_dict[name])
                matched = True

            if not matched:
                unmatched_data.append(entry)

        return matched_data, unmatched_data

    @classmethod
    def _collect_discovery_rule_tables(cls, mib_data_json_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect discovery rule tables from MIB data.

        Args:
            mib_data_json_list (List[Dict[str, Any]]): List of MIB data dictionaries.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary of discovery rule tables keyed by OID.
        """
        # Sort the list of dictionaries by OID
        mib_sorted_by_oid = sorted(mib_data_json_list, key=lambda x: x['OID'])
        
        discovery_rule_tables = {}
        current_rule = None
        
        for entry in mib_sorted_by_oid:
            if 'Table' in entry['Name'] and 'SEQUENCE OF' in entry['Type']:
                # We've found the beginning entry to create a Discovery Rule
                if current_rule:
                    # Save the previous rule if it exists
                    discovery_rule_tables[current_rule['OID']] = current_rule['entries']
                
                # Start a new rule
                current_rule = {'OID': entry['OID'], 'entries': [entry]}
            elif current_rule and entry['OID'].startswith(current_rule['OID']):
                current_rule['entries'].append(entry)
            else:
                if current_rule:
                    # Save the previous rule if it exists
                    discovery_rule_tables[current_rule['OID']] = current_rule['entries']
                    current_rule = None
        
        # Make sure we add the last rule if it exists
        if current_rule:
            discovery_rule_tables[current_rule['OID']] = current_rule['entries']

        logger.info(f'[{len(discovery_rule_tables)}] Discovery Rules found (before splitting).')

        # Split large tables into sub-discovery rules
        split_tables = cls._split_large_tables(discovery_rule_tables)

        logger.info(f'[{len(split_tables)}] Discovery Rules after splitting.')
        return split_tables

    @classmethod
    def _split_large_tables(cls, discovery_rule_tables: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Split large discovery rule tables into multiple sub-tables.

        When a table has too many OIDs to fit in one walk item, this method:
        1. Detects index/identifier OIDs
        2. Splits metric OIDs into chunks
        3. Creates multiple sub-tables, each with indices + chunk of metrics

        Args:
            discovery_rule_tables: Original discovery rule tables

        Returns:
            Dictionary with split tables (may have more entries than input)
        """
        split_tables = {}

        for table_oid, table_data in discovery_rule_tables.items():
            if len(table_data) <= 2:  # Just Table and Entry, no columns
                split_tables[table_oid] = table_data
                continue

            # Detect index OIDs
            index_oids = detect_index_oids(table_data)
            table_name = table_data[0].get('Name', 'Unknown')

            # Calculate how many OIDs (indices + metrics) fit per walk
            # Reserve space for indices
            available_slots = MAX_OIDS_PER_WALK - len(index_oids)

            if available_slots <= 0:
                logger.warning(f"Table {table_name}: Too many index OIDs ({len(index_oids)}), using all as one chunk")
                split_tables[table_oid] = table_data
                continue

            # Get metric OIDs (everything after Table, Entry, and indices)
            # Table[0], Entry[1], then index OIDs, then metrics
            num_skip = 2 + len(index_oids)
            metric_oids = table_data[num_skip:]

            # Check if splitting is needed
            if len(metric_oids) <= available_slots:
                # No splitting needed, table fits in one walk
                split_tables[table_oid] = table_data
                logger.debug(f"Table {table_name}: Fits in one walk ({len(table_data)} total OIDs)")
                continue

            # Split metrics into chunks
            metric_chunks = [metric_oids[i:i + available_slots]
                           for i in range(0, len(metric_oids), available_slots)]

            logger.info(f"Splitting {table_name}: {len(metric_oids)} metrics → {len(metric_chunks)} sub-tables")

            # Create sub-tables
            for chunk_num, metric_chunk in enumerate(metric_chunks, start=1):
                # Each sub-table: Table + Entry + index OIDs + metric chunk
                sub_table = (
                    [table_data[0], table_data[1]] +  # Table and Entry
                    index_oids +                        # Index OIDs
                    metric_chunk                        # Chunk of metrics
                )

                # Generate unique key for sub-table
                sub_key = f"{table_oid}_part{chunk_num}"
                split_tables[sub_key] = sub_table

                logger.debug(f"  Sub-table {chunk_num}: {len(sub_table)} OIDs "
                           f"({len(index_oids)} indices + {len(metric_chunk)} metrics)")

        return split_tables

    @staticmethod
    def _print_results(matched_data: List[Dict[str, Any]], unmatched_data: List[Dict[str, Any]], null_entries: List[Dict[str, Any]], entity_type: str) -> None:
        """
        Print validation results.

        Args:
            matched_data (List[Dict[str, Any]]): List of matched entries.
            unmatched_data (List[Dict[str, Any]]): List of unmatched entries.
            null_entries (List[Dict[str, Any]]): List of null entries.
            entity_type (str): Type of entity being validated (e.g., "SNMP Items", "SNMP Traps").
        """
        logger.info(f"[{len(matched_data)}] Validated {entity_type} entries")
        logger.info(f"[{len(unmatched_data)}] Missing {entity_type} entries")
        logger.info(f"[{len(null_entries)}] Null entries")

        if unmatched_data:
            logger.warning(f"The following {entity_type} entries were missing from the MIB file:")
            for entry in unmatched_data:
                logger.warning(f"  - {entry.get('Name', 'N/A')} (OID: {entry.get('OID', 'N/A')})")