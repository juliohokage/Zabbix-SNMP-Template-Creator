import os
import sys
import time
import json
import argparse
import logging
from typing import Literal

from zabbix_objects.template import Template
from utils.mib_validator import MIBValidator
from utils.logger import logger, setup_logger

def create_all_json(template: Template, include_items: bool = True, include_traps: bool = True, include_discovery_rules: bool = True) -> str:
    """
    Create a JSON representation of the template and its components.

    Args:
        template (Template): The Template object to convert to JSON.
        include_items (bool): Whether to include SNMP items in the JSON.
        include_traps (bool): Whether to include SNMP traps in the JSON.
        include_discovery_rules (bool): Whether to include discovery rules in the JSON.

    Returns:
        str: A JSON string representation of the template and its components.
    """
    template_json = template.generate_json_dict()  # Assuming this method returns a dict

    if include_items and template.snmp_items:
        snmp_item_json = [snmp_item.generate_json_dict() for snmp_item in template.snmp_items]
        template_json['zabbix_export']['templates'][0]['items'].extend(snmp_item_json)
    
    if include_traps and template.snmp_traps:
        snmp_trap_json = [snmp_trap.generate_json_dict() for snmp_trap in template.snmp_traps]
        template_json['zabbix_export']['templates'][0]['items'].extend(snmp_trap_json)
    
    if include_discovery_rules and template.discovery_rules:
        discovery_rule_json = [discovery_rule.generate_json_dict() for discovery_rule in template.discovery_rules]
        if discovery_rule_json:
            template_json['zabbix_export']['templates'][0]['discovery_rules'] = discovery_rule_json

    return json.dumps(template_json, indent=4, sort_keys=False)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Generate Zabbix templates from MIB data in Excel files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s sample_template_file.xlsx
  %(prog)s -o /path/to/output input.xlsx
  %(prog)s --log-level DEBUG input.xlsx
  %(prog)s --no-items --no-traps input.xlsx  (discovery rules only)

For more information, visit: https://github.com/Galileo-Suite/Zabbix-SNMP-Template-Creator
        '''
    )

    parser.add_argument(
        'excel_file',
        help='Path to Excel file containing MIB data'
    )

    parser.add_argument(
        '-o', '--output-dir',
        default='./created_templates',
        help='Output directory for generated templates (default: ./created_templates)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )

    parser.add_argument(
        '--no-items',
        action='store_true',
        help='Exclude SNMP items from template'
    )

    parser.add_argument(
        '--no-traps',
        action='store_true',
        help='Exclude SNMP traps from template'
    )

    parser.add_argument(
        '--no-discovery',
        action='store_true',
        help='Exclude discovery rules from template'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='Zabbix SNMP Template Generator 1.0.0'
    )

    return parser.parse_args()

def main() -> None:
    """
    Main function to process an Excel file and generate a Zabbix template JSON.

    This function:
    1. Parses command-line arguments
    2. Extracts data from the provided Excel file
    3. Creates a Template object
    4. Generates a JSON representation of the template
    5. Writes the JSON to a file
    """
    # Parse arguments
    args = parse_arguments()

    # Set log level
    log_level = getattr(logging, args.log_level)
    setup_logger('zabbix_template_generator', log_level)

    # Validate file exists
    if not os.path.exists(args.excel_file):
        logger.error(f"File '{args.excel_file}' not found.")
        sys.exit(1)

    try:
        logger.info("Extracting data from Excel...")
        snmp_items_json_list, snmp_traps_json_list, template_info_json, discovery_rule_tables = MIBValidator.extract_from_excel(args.excel_file)

        logger.info("Creating Template...")
        template = Template(template_info_json, snmp_items_json_list, snmp_traps_json_list, discovery_rule_tables)

        logger.info("Creating JSON...")
        json_template = create_all_json(
            template,
            include_items=not args.no_items,
            include_traps=not args.no_traps,
            include_discovery_rules=not args.no_discovery
        )

        logger.info("Writing JSON to file...")
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        output_dir = args.output_dir
        output_file = f'{output_dir}/{timestamp} {template.name} Template.json'

        # Check if the directory exists, if not, create it
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"Created directory: {output_dir}")
        except OSError as e:
            logger.error(f"Failed to create output directory: {e}")
            sys.exit(1)

        try:
            with open(output_file, 'w') as f:
                f.write(json_template)
        except IOError as e:
            logger.error(f"Failed to write output file: {e}")
            sys.exit(1)

        logger.info(f"JSON template saved as '{output_file}'")
        logger.info("Process completed successfully!")

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
