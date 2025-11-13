#!/usr/bin/env python3
"""
CSV Preprocessor CLI - Convert MIB Browser CSV exports to template-ready XLSX files.

Usage:
    python preprocess_csv.py <csv_file> [options]

Example:
    python preprocess_csv.py mib_export.csv
    python preprocess_csv.py mib_export.csv --output my_template.xlsx
    python preprocess_csv.py mib_export.csv --auto --no-interactive
"""

import argparse
import sys
from pathlib import Path
from utils.csv_preprocessor import CSVPreprocessor
from utils.item_suggester import ItemSuggester
from utils.logger import logger


def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print("  Zabbix SNMP Template Creator - CSV Preprocessor")
    print("  Converts MIB Browser CSV exports to template-ready XLSX files")
    print("=" * 70)
    print()


def print_preview(preview_data: dict):
    """Print preview of what will be included."""
    print("\n" + "=" * 70)
    print("  📊 MIB DATA ANALYSIS")
    print("=" * 70)

    stats = preview_data['statistics']
    print(f"\n  Total MIB Entries: {preview_data['mib_entries']}")
    print(f"  Primary MIB Module: {preview_data['primary_mib_module']}")
    print()
    print("  Breakdown:")
    print(f"    ✓ Readable Items: {stats['readable_items']}")
    print(f"    ✓ SNMP Traps: {stats['traps']}")
    print(f"    ✓ Tables: {stats['tables']}")
    print(f"    ✗ Not Accessible: {stats['not_accessible']}")
    print()

    print("  Suggested Items by Priority:")
    cat = preview_data['categorized_counts']
    print(f"    🔴 Critical: {cat['critical']}")
    print(f"    🟡 Important: {cat['important']}")
    print(f"    🔵 Informational: {cat['informational']}")
    print()

    print(f"  Auto-suggested SNMP Items: {preview_data['suggested_items_count']}")
    if preview_data['suggested_items']:
        print("  Sample items (first 10):")
        for item in preview_data['suggested_items'][:10]:
            print(f"    • {item}")
        if len(preview_data['suggested_items']) > 10:
            print(f"    ... and {len(preview_data['suggested_items']) - 10} more")
    print()

    print(f"  Auto-suggested SNMP Traps: {preview_data['suggested_traps_count']}")
    if preview_data['suggested_traps']:
        print("  Trap items:")
        for trap in preview_data['suggested_traps'][:10]:
            print(f"    • {trap}")
        if len(preview_data['suggested_traps']) > 10:
            print(f"    ... and {len(preview_data['suggested_traps']) - 10} more")

    print("\n" + "=" * 70)


def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default value."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def confirm(prompt: str, default: bool = True) -> bool:
    """Get yes/no confirmation from user."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")


def interactive_mode(csv_file: str, output_file: str = None) -> dict:
    """
    Run interactive mode to gather template information.

    Args:
        csv_file: Path to CSV file
        output_file: Optional output file path

    Returns:
        Dictionary with template configuration
    """
    print("\n📝 TEMPLATE CONFIGURATION")
    print("-" * 70)
    print("Please provide template information (press Enter for defaults):\n")

    # Get template info
    template_name = get_user_input("Template Name", "SNMP Template")
    template_group = get_user_input("Template Group", "Templates/Network Devices")
    manufacturer = get_user_input("Manufacturer", "Generic")
    device = get_user_input("Device Type", "Network Device")
    model = get_user_input("Model (optional)", "")
    macros = get_user_input("SNMP Macros", "{$SNMP_COMMUNITY}=public")
    tags = get_user_input("Tags (comma-separated)", "")

    # Determine output file
    if not output_file:
        default_output = f"{template_name.replace(' ', '_').lower()}_template.xlsx"
        output_file = get_user_input("Output File", default_output)

    print("\n🔍 ITEM SELECTION")
    print("-" * 70)

    # Get preview
    preprocessor = CSVPreprocessor()
    try:
        preview = preprocessor.get_preview_data(csv_file)
        print_preview(preview)
    except Exception as e:
        logger.error(f"Failed to preview CSV: {e}")
        print(f"\n❌ Error: {e}")
        return None

    # Ask about auto-suggestion
    use_auto_suggest = confirm("\nUse auto-suggested items and traps?", default=True)

    include_informational = True
    if use_auto_suggest:
        include_informational = confirm(
            "Include informational items (serial numbers, descriptions)?",
            default=True
        )

    return {
        'csv_file': csv_file,
        'output_file': output_file,
        'template_name': template_name,
        'template_group': template_group,
        'manufacturer': manufacturer,
        'device': device,
        'model': model,
        'macros': macros,
        'tags': tags,
        'auto_suggest': use_auto_suggest,
        'include_informational': include_informational
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert MIB Browser CSV exports to template-ready XLSX files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (recommended)
  python preprocess_csv.py mib_export.csv

  # Fully automated with defaults
  python preprocess_csv.py mib_export.csv --auto --template-name "Cisco Router"

  # Custom output location
  python preprocess_csv.py mib_export.csv --output ./templates/cisco_template.xlsx

  # Preview only (no file generation)
  python preprocess_csv.py mib_export.csv --preview-only
        """
    )

    parser.add_argument('csv_file', help='Path to MIB Browser CSV export file')
    parser.add_argument('-o', '--output', help='Output XLSX file path')
    parser.add_argument('--template-name', default='SNMP Template', help='Template name')
    parser.add_argument('--template-group', default='Templates/Network Devices',
                       help='Zabbix template group')
    parser.add_argument('--manufacturer', default='Generic', help='Device manufacturer')
    parser.add_argument('--device', default='Network Device', help='Device type')
    parser.add_argument('--model', default='', help='Device model')
    parser.add_argument('--macros', default='{$SNMP_COMMUNITY}=public', help='Template macros')
    parser.add_argument('--tags', default='', help='Template tags')
    parser.add_argument('--auto', action='store_true',
                       help='Use auto-suggestions without prompts')
    parser.add_argument('--no-informational', action='store_true',
                       help='Exclude informational items from auto-suggestions')
    parser.add_argument('--preview-only', action='store_true',
                       help='Show preview only without generating file')
    parser.add_argument('--no-interactive', action='store_true',
                       help='Disable interactive mode (use with --auto)')

    args = parser.parse_args()

    # Validate CSV file exists
    if not Path(args.csv_file).exists():
        print(f"❌ Error: CSV file not found: {args.csv_file}")
        sys.exit(1)

    print_banner()

    # Preview-only mode
    if args.preview_only:
        preprocessor = CSVPreprocessor()
        try:
            preview = preprocessor.get_preview_data(args.csv_file)
            print_preview(preview)
            print("\n✓ Preview complete. Use without --preview-only to generate XLSX file.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Failed to preview CSV: {e}")
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    # Interactive mode (if not disabled)
    if not args.no_interactive and not args.auto:
        config = interactive_mode(args.csv_file, args.output)
        if not config:
            print("\n❌ Configuration failed. Exiting.")
            sys.exit(1)
    else:
        # Non-interactive mode
        config = {
            'csv_file': args.csv_file,
            'output_file': args.output or f"{args.template_name.replace(' ', '_').lower()}_template.xlsx",
            'template_name': args.template_name,
            'template_group': args.template_group,
            'manufacturer': args.manufacturer,
            'device': args.device,
            'model': args.model,
            'macros': args.macros,
            'tags': args.tags,
            'auto_suggest': True,
            'include_informational': not args.no_informational
        }

    # Generate XLSX
    print("\n⚙️  GENERATING XLSX FILE")
    print("-" * 70)

    preprocessor = CSVPreprocessor()
    try:
        output_path = preprocessor.process_csv_to_xlsx(
            csv_path=config['csv_file'],
            output_path=config['output_file'],
            template_name=config['template_name'],
            template_group=config['template_group'],
            manufacturer=config['manufacturer'],
            device=config['device'],
            model=config['model'],
            macros=config['macros'],
            tags=config['tags'],
            auto_suggest=config['auto_suggest'],
            include_informational=config['include_informational']
        )

        print("\n" + "=" * 70)
        print("  ✅ SUCCESS!")
        print("=" * 70)
        print(f"\n  Generated file: {output_path}")
        print(f"\n  Next step:")
        print(f"    python main.py {output_path}")
        print("\n" + "=" * 70)

    except Exception as e:
        logger.error(f"Failed to generate XLSX: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
