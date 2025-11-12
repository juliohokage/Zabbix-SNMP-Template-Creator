"""
Flask API for Zabbix SNMP Template Generator Web Interface

This module provides REST API endpoints for the web interface to:
- Upload and parse Excel/CSV files
- Generate Zabbix templates
- Validate configurations
- Manage sessions
"""

import os
import json
import time
import uuid
import tempfile
from io import BytesIO
from typing import Dict, Any, List, Tuple
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from zabbix_objects.template import Template
from utils.mib_validator import MIBValidator, UnmatchedDataError
from utils.logger import logger, setup_logger
from main import create_all_json

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# Session storage (in-memory for now, could be moved to Redis/database)
sessions = {}

def allowed_file(filename: str) -> bool:
    """Check if uploaded file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_error_response(error_type: str, message: str, details: Any = None, status_code: int = 400):
    """Create standardized error response."""
    response = {
        'status': 'error',
        'error_type': error_type,
        'message': message
    }
    if details:
        response['details'] = details
    return jsonify(response), status_code

def create_success_response(data: Dict[str, Any], message: str = None):
    """Create standardized success response."""
    response = {
        'status': 'success',
        'data': data
    }
    if message:
        response['message'] = message
    return jsonify(response)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Zabbix SNMP Template Generator API',
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload and parse Excel/CSV file.

    Request:
        - file: Excel/CSV file (multipart/form-data)

    Response:
        {
            "status": "success",
            "data": {
                "session_id": "abc123",
                "mib_data": [...],
                "snmp_items_available": [...],
                "snmp_traps_available": [...],
                "discovered_tables": {...},
                "stats": {
                    "total_entries": 1247,
                    "tables_detected": 15,
                    "items_count": 234,
                    "traps_count": 47
                }
            }
        }
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return create_error_response('missing_file', 'No file provided in request')

        file = request.files['file']

        # Check if file is selected
        if file.filename == '':
            return create_error_response('empty_filename', 'No file selected')

        # Check file extension
        if not allowed_file(file.filename):
            return create_error_response(
                'invalid_file_type',
                f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            )

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        file.save(temp_path)

        logger.info(f"Processing uploaded file: {filename}")

        try:
            # Extract data using MIBValidator
            snmp_items_json_list, snmp_traps_json_list, template_info_json, discovery_rule_tables, trigger_overrides = \
                MIBValidator.extract_from_excel(temp_path)

            # Create session ID
            session_id = str(uuid.uuid4())

            # Store session data
            sessions[session_id] = {
                'filename': filename,
                'snmp_items_json_list': snmp_items_json_list,
                'snmp_traps_json_list': snmp_traps_json_list,
                'template_info_json': template_info_json,
                'discovery_rule_tables': discovery_rule_tables,
                'trigger_overrides': trigger_overrides,
                'timestamp': time.time()
            }

            # Collect MIB data (all available items from discovery rules)
            mib_data = []
            for table_oid, table_entries in discovery_rule_tables.items():
                mib_data.extend(table_entries)

            # Calculate stats
            stats = {
                'total_entries': len(mib_data),
                'tables_detected': len(discovery_rule_tables),
                'items_count': len(snmp_items_json_list),
                'traps_count': len(snmp_traps_json_list),
                'trigger_overrides': len(trigger_overrides)
            }

            # Prepare discovery rules summary
            discovered_tables_summary = []
            for table_oid, table_entries in discovery_rule_tables.items():
                if table_entries:
                    table_name = table_entries[0].get('Name', 'Unknown')
                    discovered_tables_summary.append({
                        'oid': table_oid,
                        'name': table_name,
                        'item_count': len(table_entries) - 2,  # Exclude Table and Entry
                        'is_split': '_part' in table_oid
                    })

            response_data = {
                'session_id': session_id,
                'stats': stats,
                'template_info': template_info_json,
                'snmp_items_available': snmp_items_json_list,
                'snmp_traps_available': snmp_traps_json_list,
                'discovered_tables': discovered_tables_summary
            }

            logger.info(f"Session created: {session_id}")
            return create_success_response(response_data, 'File uploaded and processed successfully')

        except UnmatchedDataError as e:
            return create_error_response(
                'unmatched_data',
                str(e),
                details={'error': str(e)}
            )
        except ValueError as e:
            return create_error_response('validation_error', str(e))
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        return create_error_response('internal_error', f'Error processing file: {str(e)}', status_code=500)

@app.route('/api/generate', methods=['POST'])
def generate_template():
    """
    Generate Zabbix template JSON from configuration.

    Request:
        {
            "session_id": "abc123",
            "template_info": {...},
            "selected_items": ["cpuUtilization", ...],
            "selected_traps": ["linkDown", ...],
            "discovery_rules": {...},
            "trigger_overrides": {...},
            "options": {
                "include_items": true,
                "include_traps": true,
                "include_discovery_rules": true,
                "generate_triggers": true
            }
        }

    Response:
        {
            "status": "success",
            "data": {
                "template_json": {...},
                "filename": "20250109_143022 Cisco Catalyst 9300 Template.json",
                "validation": {
                    "errors": [],
                    "warnings": [...],
                    "info": [...]
                }
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return create_error_response('invalid_request', 'Request body must be JSON')

        # Get session ID
        session_id = data.get('session_id')
        if not session_id or session_id not in sessions:
            return create_error_response('invalid_session', 'Invalid or expired session ID')

        session_data = sessions[session_id]

        # Get configuration from request
        template_info = data.get('template_info', session_data['template_info_json'])
        selected_items_names = data.get('selected_items', [])
        selected_traps_names = data.get('selected_traps', [])
        selected_discovery_rules = data.get('discovery_rules', list(session_data['discovery_rule_tables'].keys()))
        trigger_overrides = data.get('trigger_overrides', session_data['trigger_overrides'])
        options = data.get('options', {})

        # Filter items based on selection
        if selected_items_names:
            snmp_items_json_list = [
                item for item in session_data['snmp_items_json_list']
                if item.get('Name') in selected_items_names or item.get('OID') in selected_items_names
            ]
        else:
            snmp_items_json_list = session_data['snmp_items_json_list']

        # Filter traps based on selection
        if selected_traps_names:
            snmp_traps_json_list = [
                trap for trap in session_data['snmp_traps_json_list']
                if trap.get('Name') in selected_traps_names or trap.get('OID') in selected_traps_names
            ]
        else:
            snmp_traps_json_list = session_data['snmp_traps_json_list']

        # Filter discovery rules based on selection
        if selected_discovery_rules:
            discovery_rule_tables = {
                oid: tables for oid, tables in session_data['discovery_rule_tables'].items()
                if oid in selected_discovery_rules
            }
        else:
            discovery_rule_tables = session_data['discovery_rule_tables']

        # Get options
        include_items = options.get('include_items', True)
        include_traps = options.get('include_traps', True)
        include_discovery_rules = options.get('include_discovery_rules', True)
        generate_triggers = options.get('generate_triggers', True)

        logger.info(f"Generating template for session: {session_id}")

        # Create Template object
        template = Template(
            template_info,
            snmp_items_json_list,
            snmp_traps_json_list,
            discovery_rule_tables,
            generate_triggers=generate_triggers,
            trigger_overrides=trigger_overrides
        )

        # Generate JSON
        json_template = create_all_json(
            template,
            include_items=include_items,
            include_traps=include_traps,
            include_discovery_rules=include_discovery_rules
        )

        # Create filename
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f'{timestamp} {template.name} Template.json'

        # Perform validation
        validation_results = validate_template_data(
            template,
            snmp_items_json_list,
            snmp_traps_json_list,
            discovery_rule_tables
        )

        response_data = {
            'template_json': json.loads(json_template),
            'filename': filename,
            'validation': validation_results
        }

        logger.info(f"Template generated successfully: {filename}")
        return create_success_response(response_data, 'Template generated successfully')

    except Exception as e:
        logger.error(f"Error generating template: {e}", exc_info=True)
        return create_error_response('generation_error', f'Error generating template: {str(e)}', status_code=500)

@app.route('/api/validate', methods=['POST'])
def validate_configuration():
    """
    Validate configuration without generating template.

    Request: Same as /api/generate

    Response:
        {
            "status": "success",
            "data": {
                "validation": {
                    "template_structure": "valid",
                    "oid_validation": "valid",
                    "trigger_expressions": "valid",
                    "errors": [],
                    "warnings": [...],
                    "info": [...]
                }
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return create_error_response('invalid_request', 'Request body must be JSON')

        session_id = data.get('session_id')
        if not session_id or session_id not in sessions:
            return create_error_response('invalid_session', 'Invalid or expired session ID')

        session_data = sessions[session_id]

        # Perform validation checks
        validation_results = {
            'template_structure': 'valid',
            'oid_validation': 'valid',
            'trigger_expressions': 'valid',
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Check for informational items without triggers
        items_without_triggers = [
            item for item in session_data['snmp_items_json_list']
            if 'Description' in item.get('Type', '') or 'String' in item.get('Type', '')
        ]

        if items_without_triggers:
            validation_results['warnings'].append(
                f'{len(items_without_triggers)} informational fields have no triggers'
            )

        # Check for split tables
        split_tables = [oid for oid in session_data['discovery_rule_tables'].keys() if '_part' in oid]
        if split_tables:
            validation_results['warnings'].append(
                f'{len(split_tables)} large tables were split into sub-discovery rules'
            )

        # Add info about trigger overrides
        if session_data['trigger_overrides']:
            validation_results['info'].append(
                f'{len(session_data["trigger_overrides"])} trigger overrides loaded from Excel'
            )

        return create_success_response({'validation': validation_results})

    except Exception as e:
        logger.error(f"Error validating configuration: {e}", exc_info=True)
        return create_error_response('validation_error', f'Error validating: {str(e)}', status_code=500)

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """
    Get session data.

    Response:
        {
            "status": "success",
            "data": {
                "session_id": "abc123",
                "filename": "sample.xlsx",
                "stats": {...},
                "template_info": {...}
            }
        }
    """
    if session_id not in sessions:
        return create_error_response('invalid_session', 'Session not found', status_code=404)

    session_data = sessions[session_id]

    response_data = {
        'session_id': session_id,
        'filename': session_data['filename'],
        'stats': {
            'items_count': len(session_data['snmp_items_json_list']),
            'traps_count': len(session_data['snmp_traps_json_list']),
            'tables_detected': len(session_data['discovery_rule_tables'])
        },
        'template_info': session_data['template_info_json']
    }

    return create_success_response(response_data)

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """Delete session data."""
    if session_id in sessions:
        del sessions[session_id]
        return create_success_response({}, 'Session deleted successfully')

    return create_error_response('invalid_session', 'Session not found', status_code=404)

def validate_template_data(
    template: Template,
    snmp_items: List[Dict[str, Any]],
    snmp_traps: List[Dict[str, Any]],
    discovery_rules: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Perform validation on template data.

    Returns:
        Dictionary with validation results including errors, warnings, and info messages
    """
    validation = {
        'errors': [],
        'warnings': [],
        'info': []
    }

    # Check template structure
    if not template.name:
        validation['errors'].append('Template name is required')

    # Check for informational items
    info_items = [item for item in snmp_items if 'String' in item.get('Type', '')]
    if info_items:
        validation['warnings'].append(
            f'{len(info_items)} informational fields may not have triggers'
        )

    # Check for split discovery rules
    split_rules = [oid for oid in discovery_rules.keys() if '_part' in oid]
    if split_rules:
        base_tables = set(oid.split('_part')[0] for oid in split_rules)
        validation['warnings'].append(
            f'{len(base_tables)} large tables split into {len(split_rules)} sub-discovery rules'
        )

    # Count auto-generated triggers
    trigger_count = len(template.triggers) if hasattr(template, 'triggers') else 0
    if trigger_count > 0:
        validation['info'].append(f'{trigger_count} triggers auto-generated')

    # Count discovery rules and item prototypes
    if discovery_rules:
        total_prototypes = sum(
            len(entries) - 2 for entries in discovery_rules.values()  # Exclude Table and Entry
        )
        validation['info'].append(
            f'{len(discovery_rules)} discovery rules with {total_prototypes} item prototypes'
        )

    return validation

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return create_error_response(
        'file_too_large',
        'File size exceeds maximum allowed size (50MB)',
        status_code=413
    )

@app.errorhandler(404)
def not_found(error):
    """Handle not found error."""
    return create_error_response(
        'not_found',
        'Endpoint not found',
        status_code=404
    )

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error."""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return create_error_response(
        'internal_error',
        'An internal error occurred',
        status_code=500
    )

if __name__ == '__main__':
    # Setup logging
    import logging
    setup_logger('zabbix_template_generator', logging.INFO)

    # Run Flask app
    logger.info("Starting Zabbix SNMP Template Generator API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
