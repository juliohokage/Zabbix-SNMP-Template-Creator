"""
CSV Preprocessor - Convert MIB Browser CSV exports to template-ready XLSX files.

This module handles the conversion from raw CSV MIB exports to properly formatted
Excel files with all required sheets for template generation.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from utils.logger import logger
from utils.item_suggester import ItemSuggester


class CSVPreprocessor:
    """
    Preprocesses CSV files from MIB Browser tools into template-ready XLSX files.
    """

    # Expected columns from MIB Browser CSV exports (flexible - not all required)
    EXPECTED_CSV_COLUMNS = {
        'Name', 'OID', 'Type', 'Access', 'Description',
        'MIB Module', 'Full Name', 'Indexes', 'Syntax'
    }

    # Required columns for MIB Data sheet
    REQUIRED_MIB_COLUMNS = ['Name', 'OID', 'Type']

    # Standard column mapping for different MIB browser tools
    COLUMN_MAPPINGS = {
        'Object Name': 'Name',
        'Object Identifier': 'OID',
        'Data Type': 'Type',
        'Max Access': 'Access',
        'Module': 'MIB Module',
        'Object Description': 'Description',
    }

    def __init__(self):
        self.suggester = ItemSuggester()

    def process_csv_to_xlsx(self,
                           csv_path: str,
                           output_path: str,
                           template_name: str,
                           template_group: str = "Templates/Network Devices",
                           manufacturer: str = "",
                           device: str = "",
                           model: str = "",
                           macros: str = "{$SNMP_COMMUNITY}=public",
                           tags: str = "",
                           selected_items: Optional[List[str]] = None,
                           selected_traps: Optional[List[str]] = None,
                           auto_suggest: bool = True,
                           include_informational: bool = True) -> str:
        """
        Process CSV file and generate XLSX template file.

        Args:
            csv_path: Path to input CSV file
            output_path: Path for output XLSX file
            template_name: Name of the template
            template_group: Zabbix template group
            manufacturer: Device manufacturer
            device: Device type
            model: Device model
            macros: Template macros
            tags: Template tags
            selected_items: List of item names to include (None = auto-suggest)
            selected_traps: List of trap names to include (None = auto-suggest)
            auto_suggest: Whether to auto-suggest items if not provided
            include_informational: Include informational items in suggestions

        Returns:
            Path to generated XLSX file

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV is malformed or missing required data
        """
        logger.info(f"Processing CSV file: {csv_path}")

        # Step 1: Read and normalize CSV
        mib_data = self._read_and_normalize_csv(csv_path)
        logger.info(f"Loaded {len(mib_data)} MIB entries from CSV")

        # Step 2: Get statistics
        stats = self.suggester.get_statistics(mib_data)
        logger.info(f"MIB Statistics: {stats}")

        # Step 3: Suggest or use provided items
        if selected_items is None and auto_suggest:
            suggested_items = self.suggester.suggest_snmp_items(
                mib_data,
                include_informational=include_informational
            )
            items_data = self._format_items_for_sheet(suggested_items)
        elif selected_items:
            items_data = self._get_items_by_names(mib_data, selected_items)
        else:
            items_data = []

        # Step 4: Suggest or use provided traps
        if selected_traps is None and auto_suggest:
            suggested_traps = self.suggester.suggest_snmp_traps(mib_data)
            traps_data = self._format_items_for_sheet(suggested_traps)
        elif selected_traps:
            traps_data = self._get_items_by_names(mib_data, selected_traps)
        else:
            traps_data = []

        # Step 5: Create template information
        template_info = self._create_template_info(
            template_name, template_group, manufacturer,
            device, model, macros, tags
        )

        # Step 6: Prepare MIB data sheet
        mib_data_formatted = self._format_mib_data(mib_data)

        # Step 7: Generate XLSX file
        output_file = self._generate_xlsx(
            output_path,
            template_info,
            items_data,
            traps_data,
            mib_data_formatted,
            mib_data
        )

        logger.info(f"Successfully generated XLSX: {output_file}")
        logger.info(f"  - Template: {template_name}")
        logger.info(f"  - Items: {len(items_data)}")
        logger.info(f"  - Traps: {len(traps_data)}")

        return output_file

    def _read_and_normalize_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Read CSV file and normalize column names.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of normalized MIB data dictionaries

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV is malformed
        """
        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        try:
            # Try reading with different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV file with any standard encoding")

        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")

        # Normalize column names
        df = self._normalize_column_names(df)

        # Validate required columns
        self._validate_columns(df)

        # Convert to dict list
        df = df.where(pd.notnull(df), None)
        mib_data = df.to_dict('records')

        # Filter out completely empty rows
        mib_data = [row for row in mib_data if any(v for v in row.values() if v)]

        return mib_data

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to standard format.

        Args:
            df: Input dataframe

        Returns:
            Dataframe with normalized column names
        """
        # Apply mappings
        df = df.rename(columns=self.COLUMN_MAPPINGS)

        # Ensure core columns exist (create empty if missing)
        for col in self.REQUIRED_MIB_COLUMNS:
            if col not in df.columns:
                # Try to find it with different case
                matching = [c for c in df.columns if c.lower() == col.lower()]
                if matching:
                    df = df.rename(columns={matching[0]: col})

        return df

    def _validate_columns(self, df: pd.DataFrame):
        """
        Validate that required columns are present.

        Args:
            df: Input dataframe

        Raises:
            ValueError: If required columns are missing
        """
        missing = [col for col in self.REQUIRED_MIB_COLUMNS if col not in df.columns]

        if missing:
            available = list(df.columns)
            raise ValueError(
                f"CSV is missing required columns: {missing}\n"
                f"Available columns: {available}\n"
                f"Required columns: {list(self.REQUIRED_MIB_COLUMNS)}"
            )

    def _format_items_for_sheet(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format items for SNMP Items or SNMP Traps sheet.

        Args:
            items: List of item dictionaries

        Returns:
            List formatted for Excel sheet with Name and OID columns
        """
        formatted = []
        for item in items:
            formatted.append({
                'Name': item.get('Name'),
                'OID': item.get('OID')
            })
        return formatted

    def _get_items_by_names(self, mib_data: List[Dict[str, Any]],
                           names: List[str]) -> List[Dict[str, Any]]:
        """
        Get items from MIB data by names.

        Args:
            mib_data: Full MIB data
            names: List of item names to include

        Returns:
            List of items formatted for sheet
        """
        name_dict = {item.get('Name'): item for item in mib_data}
        selected = []

        for name in names:
            if name in name_dict:
                selected.append({
                    'Name': name_dict[name].get('Name'),
                    'OID': name_dict[name].get('OID')
                })
            else:
                logger.warning(f"Item '{name}' not found in MIB data")

        return selected

    def _create_template_info(self, template_name: str, template_group: str,
                             manufacturer: str, device: str, model: str,
                             macros: str, tags: str) -> Dict[str, str]:
        """
        Create template information dictionary.

        Args:
            template_name: Template name
            template_group: Template group
            manufacturer: Manufacturer
            device: Device type
            model: Model
            macros: Macros string
            tags: Tags string

        Returns:
            Template info dictionary
        """
        return {
            'Group': template_group,
            'Manufacturer': manufacturer or 'Generic',
            'Device': device or 'Network Device',
            'Model': model or '',
            'Macros': macros or '',
            'Tags': tags or ''
        }

    def _format_mib_data(self, mib_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format MIB data for the MIB Data sheet.

        Ensures proper column order and includes all necessary fields.

        Args:
            mib_data: Raw MIB data

        Returns:
            Formatted MIB data
        """
        # Define desired column order
        columns = ['MIB Module', 'OID', 'Name', 'Description', 'Type', 'Syntax']

        formatted = []
        for entry in mib_data:
            formatted_entry = {}
            for col in columns:
                formatted_entry[col] = entry.get(col, '')
            formatted.append(formatted_entry)

        return formatted

    def _generate_xlsx(self, output_path: str,
                      template_info: Dict[str, str],
                      items_data: List[Dict[str, Any]],
                      traps_data: List[Dict[str, Any]],
                      mib_data: List[Dict[str, Any]],
                      raw_mib_data: List[Dict[str, Any]]) -> str:
        """
        Generate the XLSX file with all required sheets.

        Args:
            output_path: Output file path
            template_info: Template information
            items_data: SNMP items data
            traps_data: SNMP traps data
            mib_data: Formatted MIB data
            raw_mib_data: Raw MIB data (for sheet naming)

        Returns:
            Path to generated file
        """
        # Auto-generate filename if directory provided
        if Path(output_path).is_dir():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            template_name = template_info.get('Group', 'Template').split('/')[-1]
            filename = f"{timestamp}_{template_name}_preprocessed.xlsx"
            output_path = str(Path(output_path) / filename)

        # Ensure .xlsx extension
        if not output_path.endswith('.xlsx'):
            output_path += '.xlsx'

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Template Information
            df_template = pd.DataFrame([template_info])
            df_template.to_excel(writer, sheet_name='Template Information', index=False)

            # Sheet 2: SNMP Items
            if items_data:
                df_items = pd.DataFrame(items_data)
            else:
                # Create empty sheet with headers
                df_items = pd.DataFrame(columns=['Name', 'OID'])
            df_items.to_excel(writer, sheet_name='SNMP Items', index=False)

            # Sheet 3: SNMP Traps
            if traps_data:
                df_traps = pd.DataFrame(traps_data)
            else:
                # Create empty sheet with headers
                df_traps = pd.DataFrame(columns=['Name', 'OID'])
            df_traps.to_excel(writer, sheet_name='SNMP Traps', index=False)

            # Sheet 4: MIB Data (use first MIB module name if available)
            mib_module_name = self._get_primary_mib_module(raw_mib_data)
            df_mib = pd.DataFrame(mib_data)
            df_mib.to_excel(writer, sheet_name=mib_module_name, index=False)

        return output_path

    def _get_primary_mib_module(self, mib_data: List[Dict[str, Any]]) -> str:
        """
        Get the primary MIB module name from data.

        Args:
            mib_data: MIB data list

        Returns:
            Primary MIB module name or 'MIB Data'
        """
        # Count occurrences of each MIB module
        module_counts = {}
        for entry in mib_data:
            module = entry.get('MIB Module', '')
            if module:
                module_counts[module] = module_counts.get(module, 0) + 1

        # Return most common, or default
        if module_counts:
            primary = max(module_counts.items(), key=lambda x: x[1])[0]
            # Limit length and ensure valid sheet name
            return primary[:31] if len(primary) <= 31 else primary[:28] + '...'

        return 'MIB Data'

    def get_preview_data(self, csv_path: str) -> Dict[str, Any]:
        """
        Get preview data from CSV without generating XLSX.

        Useful for showing user what will be included before final generation.

        Args:
            csv_path: Path to CSV file

        Returns:
            Dictionary with preview information
        """
        mib_data = self._read_and_normalize_csv(csv_path)
        stats = self.suggester.get_statistics(mib_data)

        suggested_items = self.suggester.suggest_snmp_items(mib_data)
        suggested_traps = self.suggester.suggest_snmp_traps(mib_data)

        categorized = self.suggester.categorize_items(suggested_items)

        return {
            'statistics': stats,
            'mib_entries': len(mib_data),
            'suggested_items_count': len(suggested_items),
            'suggested_traps_count': len(suggested_traps),
            'suggested_items': [item.get('Name') for item in suggested_items[:20]],  # First 20
            'suggested_traps': [trap.get('Name') for trap in suggested_traps],
            'categorized_counts': {
                'critical': len(categorized['critical']),
                'important': len(categorized['important']),
                'informational': len(categorized['informational'])
            },
            'primary_mib_module': self._get_primary_mib_module(mib_data)
        }
