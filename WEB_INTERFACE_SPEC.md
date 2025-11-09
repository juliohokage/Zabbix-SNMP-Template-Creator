# Web Interface Specification

This document outlines the design and implementation plan for the Zabbix SNMP Template Generator web interface.

## Table of Contents
- [Overview](#overview)
- [UI/UX Design](#uiux-design)
- [Technical Architecture](#technical-architecture)
- [Implementation Plan](#implementation-plan)
- [Deployment](#deployment)

---

## Overview

### Goal
Provide a user-friendly web interface for generating Zabbix SNMP templates from MIB Browser CSV exports, eliminating the need for manual Excel file formatting and command-line usage.

### Key Features
- Drag-and-drop CSV file upload
- Step-by-step wizard interface
- Interactive item/trap selection
- Discovery rule preview and configuration
- Trigger customization
- Real-time validation
- JSON template download

### Validated Decisions
- ✅ Remove Tags Section (auto-generated from template info)
- ✅ Docker container deployment
- ✅ Minimal refactoring needed (~10-15% of existing code)
- ✅ Multi-step wizard approach
- ✅ Focus on CSV input (XLSX preprocessing is separate feature)

---

## UI/UX Design

### Overall Layout

Multi-step wizard with left navigation sidebar showing progress:

```
┌─────────────────┬──────────────────────────────────┐
│   Navigation    │                                  │
│                 │                                  │
│ 1. ✓ Upload     │        Main Content Area         │
│ 2. → Configure  │                                  │
│ 3.   Items      │                                  │
│ 4.   Discovery  │                                  │
│ 5.   Triggers   │                                  │
│ 6.   Review     │                                  │
│                 │                                  │
└─────────────────┴──────────────────────────────────┘
```

---

### Step 1: File Upload & Import

#### Visual Elements
- **Large drag-and-drop zone**: "Drop your MIB Browser CSV export here"
- **Browse files button**: Alternative to drag-and-drop
- **Sample file link**: Download `sample_template_file.xlsx` as reference

#### Functionality
- Accept CSV file upload
- Auto-detect columns (OID, Name, Description, Type, Syntax)
- Show preview table with first 20 rows
- Display stats: "1,247 MIB entries loaded, 15 tables detected"

#### Column Mapping Interface
If CSV columns don't match expected format:
```
CSV Column          →    Maps to
[Object ID    ▼]    →    OID
[Object Name  ▼]    →    Name
[Data Type    ▼]    →    Type
[Syntax Info  ▼]    →    Syntax
[Description  ▼]    →    Description
```

#### Validation
- ⚠️ Warning if required columns missing
- ✓ Success indicator when file loads correctly
- Auto-detect MIB module from filename or content

---

### Step 2: Template Configuration

#### Form Sections

**Basic Information:**
```
Template Name:     [____________________________]
Template Group:    [____________________________]
Device Type:       [____________________________]
Manufacturer:      [____________________________]
Model:             [____________________________]
```

**SNMP Macros:**
```
┌─ Macros ──────────────────────────────────────┐
│ {$SNMP_COMMUNITY}  =  [public            ]  ✕ │
│ {$IFINDEX.MATCHES} =  [.*                ]  ✕ │
│                                     [+ Add]    │
└────────────────────────────────────────────────┘
```

#### Behavior
- Pre-filled defaults where possible
- Add/remove macros dynamically
- Validation: Template name required, no special characters
- Auto-generate template group suggestion based on manufacturer

---

### Step 3: SNMP Items & Traps Selection

#### Two-Panel Layout

**Left Panel - Available MIB Items:**
```
┌─ MIB Data ─────────────────────────────────────────────┐
│ Search: [                         ] 🔍                 │
│ Filter:  [ ] Status  [ ] Counters  [✓] Metrics         │
│                                                         │
│ ☐ Select All (showing 15 of 1,247)                     │
│                                                         │
│ □ sysUpTime          1.3.6.1.2.1.1.3.0      TimeTicks  │
│ ☑ cpuUtilization     1.3.6.1.4.1...         Gauge32    │
│ ☑ memoryUtilization  1.3.6.1.4.1...         Gauge32    │
│ □ ifOperStatus       1.3.6.1.2.1.2.2.1.8    INTEGER    │
│                                              [Load More]│
└─────────────────────────────────────────────────────────┘
```

**Right Panel - Selected Items:**
```
┌─ Selected SNMP Items (2) ──────────────────────────────┐
│                                                         │
│ ⚡ cpuUtilization                                [✕]    │
│    OID: 1.3.6.1.4.1.9.9.109.1.1.1.1.7                  │
│    Type: Gauge32  |  Trigger: ✓ Auto (CPU > 90%)      │
│    [Edit Trigger]                                      │
│                                                         │
│ ⚡ memoryUtilization                             [✕]    │
│    OID: 1.3.6.1.4.1.9.9.48.1.1.1.5                     │
│    Type: Gauge32  |  Trigger: ✓ Auto (Memory > 90%)   │
│    [Edit Trigger]                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Features
- Search by OID or name
- Filter by type (Status, Counters, Metrics, Informational)
- Visual indicator (⚡) for items that will auto-generate triggers
- Quick preview of auto-detected trigger logic
- Checkbox selection with "Select All" option
- Drag-and-drop to reorder selected items
- Remove items with [✕] button

#### SNMP Traps Tab
Similar interface with:
- List of trap OIDs from MIB data
- Search by trap name
- Multi-select with checkboxes
- Preview of trap configuration

---

### Step 4: Discovery Rules Configuration

#### Visual Representation of Detected Tables

```
┌─ Detected Discovery Rules (3) ─────────────────────────┐
│                                                         │
│ 🔍 ifTable (Interface Table)               [✓ Include] │
│    Master OID: 1.3.6.1.2.1.2.2                         │
│    Index: {#IFINDEX}, {#IFDESCR}                       │
│    ├─ 15 Item Prototypes                               │
│    ├─ 5 Trigger Prototypes                             │
│    └─ [Configure ▼]                                    │
│                                                         │
│    ┌─ Item Prototypes ─────────────────────────────┐   │
│    │ ☑ ifOperStatus      → Trigger: Link down      │   │
│    │ ☑ ifInOctets        → Graph: Traffic          │   │
│    │ ☑ ifOutOctets       → Graph: Traffic          │   │
│    │ ☑ ifInErrors        → Trigger: Error rate     │   │
│    │ □ ifPhysAddress     (Informational)           │   │
│    │                               [Show all (15)]  │   │
│    └────────────────────────────────────────────────┘   │
│                                                         │
│ 🔍 entPhysicalTable                        [✓ Include] │
│    Master OID: 1.3.6.1.2.1.47.1.1.1                    │
│    ⚠ Large table (127 items) → Split into 3 sub-rules │
│    [Configure ▼]                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Features
- Auto-detected discovery rules (from MIB tables with "SEQUENCE OF")
- Expand/collapse each discovery rule details
- Include/exclude entire discovery rule
- Select which item prototypes to include
- Preview trigger conditions for each prototype
- Visual warning for split tables with explanation
- Edit LLD macro names if needed

#### Information Display
- Number of item prototypes per rule
- Number of auto-generated trigger prototypes
- Index detection results ({#IFINDEX}, {#IFDESCR}, etc.)
- Warning badges for large tables requiring splitting

---

### Step 5: Trigger Customization

#### Trigger List with Inline Editing

```
┌─ Triggers (8 auto-generated) ──────────────────────────┐
│                                                         │
│ [Items] [Item Prototypes]                              │
│                                                         │
│ ⚠ cpuUtilization > threshold                          │
│   Expression: min(/Template/cpu.util,5m) > {$CPU.MAX}  │
│   Severity:   [High        ▼]                          │
│   Threshold:  [90] %                                    │
│   [Advanced ▼]                                         │
│                                                         │
│ ⚠ memoryUtilization > threshold                       │
│   Expression: min(/Template/mem.util,5m) > {$MEM.MAX}  │
│   Severity:   [High        ▼]                          │
│   Threshold:  [90] %                                    │
│   [Advanced ▼]                                         │
│                                                         │
│ ─── Item Prototypes ───────────────────────────────    │
│                                                         │
│ ⚠ {#IFINDEX}: Interface is down                       │
│   Expression: count(...ifOperStatus,#3,"ne",1)>=2      │
│   Severity:   [Average     ▼]                          │
│   OK Value:   [1]                                       │
│   [Disable]  [Advanced ▼]                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Features
- Tab separation: Items vs Item Prototypes
- Quick edit mode: Change threshold, severity
- Advanced mode: Full expression editor (expandable)
- Disable individual triggers
- "Reset to auto-detected" button
- Color-coded severity indicators
- Preview of macro values

#### Trigger Information
- Auto-generated expression preview
- Trigger type (state, threshold, rate)
- Associated macro name and value
- Description template

---

### Step 6: Preview & Generate

#### Three-Tab Interface

**Tab 1: Summary**
```
┌─ Template Summary ──────────────────────────────────────┐
│                                                         │
│ Template Name:        Cisco Catalyst 9300              │
│ Template Group:       Templates/Network Devices/Cisco  │
│ Manufacturer:         Cisco                             │
│ Device Type:          Switch                            │
│                                                         │
│ SNMP Items:           12                               │
│ SNMP Traps:           3                                │
│ Discovery Rules:      3                                │
│ Item Prototypes:      47                               │
│ Triggers:             8                                │
│ Trigger Prototypes:   15                               │
│ Value Mappings:       6                                │
│ Macros:               5                                │
│                                                         │
│ ✓ All validations passed                               │
│                                                         │
│ [← Back to Edit]      [Generate & Download →]          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Tab 2: JSON Preview**
```
┌─ Generated JSON Preview ────────────────────────────────┐
│                                                         │
│ {                                                       │
│   "zabbix_export": {                                    │
│     "version": "7.0",                                   │
│     "templates": [{                                     │
│       "template": "Cisco Catalyst 9300",                │
│       "groups": [{"name": "Templates/Network..."}],     │
│       "items": [...],                                   │
│       "discovery_rules": [...],                         │
│       ...                                               │
│     }]                                                  │
│   }                                                     │
│ }                                                       │
│                                                         │
│ [Copy to Clipboard] [Download JSON]                    │
└─────────────────────────────────────────────────────────┘
```

**Tab 3: Validation Results**
```
┌─ Validation Results ────────────────────────────────────┐
│                                                         │
│ ✓ Template structure valid                             │
│ ✓ All OIDs validated against MIB data                  │
│ ✓ Trigger expressions syntax valid                     │
│ ✓ Discovery rule indices detected                      │
│ ✓ Value mappings generated                             │
│                                                         │
│ ⚠ 2 warnings:                                           │
│   • ifPhysAddress has no trigger (informational field)  │
│   • Large table split into 3 discovery rules           │
│                                                         │
│ ℹ 1 info:                                               │
│   • 6 value mappings auto-generated from enum syntax    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Features
- Real-time JSON generation preview
- Syntax-highlighted JSON viewer
- Copy to clipboard functionality
- Download as timestamped JSON file
- Validation status with error/warning/info levels
- Back button to edit any step

---

### Additional UI Components

#### Top Navigation Bar
```
[Logo] Zabbix SNMP Template Generator    [Save Draft] [Export Config] [Help ?]
```

**Features:**
- **Save Draft**: Save configuration to browser localStorage, resume later
- **Export Config**: Download current configuration as JSON (can be loaded later)
- **Help**: Context-sensitive help system

#### Help System
- Tooltip icons (?) throughout interface
- "What's this?" popovers with explanations
- Link to full documentation
- Inline examples

#### Real-time Validation
- Inline error messages in red
- Success indicators in green
- Warning badges on navigation steps for incomplete sections
- "Next" button disabled until section valid

#### Progress Indicators
- Checkmarks on completed steps in sidebar
- Current step highlighted
- Jump to any completed step by clicking

#### Responsive Design
- Desktop-first (1280px+ optimal)
- Tablet support (768px+)
- Collapsible sidebars for smaller screens
- Not optimized for phones (too complex)

#### Theme
- Light/dark mode toggle
- Clean, modern design
- Zabbix color scheme compatibility

---

## Technical Architecture

### Overview
Minimal refactoring approach leveraging existing well-structured Python codebase.

### Backend Architecture

#### Refactoring Assessment
- **Core logic changes**: 0% (no changes needed)
- **File handling modifications**: 5% (one new method in mib_validator.py)
- **Error handling for API**: 10% (wrap existing exceptions)
- **New API routes**: 15% (new wrapper code)

#### Changes Required

**1. File Upload Handling (mib_validator.py)**
```python
@classmethod
def extract_from_uploaded_file(cls, file_stream, filename):
    """
    Extract data from uploaded file stream instead of file path.

    Args:
        file_stream: File-like object from upload
        filename: Original filename for reference

    Returns:
        Same as extract_from_excel()
    """
    # Use pandas.read_excel() with file stream
    # Rest of logic remains unchanged
```

**2. API Layer (New file: api.py ~150-200 lines)**
```python
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from utils.mib_validator import MIBValidator
from zabbix_objects.template import Template
import tempfile
import json

app = Flask(__name__)
CORS(app)

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """Upload and parse CSV/XLSX file"""
    try:
        file = request.files['file']
        # Process with MIBValidator
        # Return parsed data + stats
        return jsonify({
            'status': 'success',
            'data': {...},
            'stats': {
                'total_entries': 1247,
                'tables_detected': 15,
                'items_count': 234
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/generate', methods=['POST'])
def generate_template():
    """Generate Zabbix template JSON from configuration"""
    try:
        config = request.json
        # Create Template object
        # Generate JSON
        # Return result
        return jsonify({
            'status': 'success',
            'template_json': {...},
            'validation': {...}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/validate', methods=['POST'])
def validate_configuration():
    """Validate configuration without generating"""
    # Run validation checks
    # Return warnings/errors
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**3. Error Handling Wrapper**
```python
# Wrap existing exceptions for JSON API responses
try:
    result = MIBValidator.extract_from_excel(...)
except UnmatchedDataError as e:
    return jsonify({
        'status': 'error',
        'error_type': 'unmatched_data',
        'message': str(e),
        'unmatched_items': e.unmatched_items
    }), 400
```

### API Endpoints

#### 1. File Upload & Parsing
```
POST /api/upload
Content-Type: multipart/form-data

Request:
- file: CSV/XLSX file

Response:
{
  "status": "success",
  "session_id": "abc123",
  "mib_data": [...],
  "stats": {
    "total_entries": 1247,
    "tables_detected": 15,
    "snmp_items_available": 1200,
    "traps_available": 47
  },
  "discovered_tables": [...]
}
```

#### 2. Template Generation
```
POST /api/generate
Content-Type: application/json

Request:
{
  "session_id": "abc123",
  "template_info": {
    "name": "Cisco Catalyst 9300",
    "group": "Templates/Network Devices/Cisco",
    "manufacturer": "Cisco",
    "device": "Switch",
    "model": "Catalyst 9300",
    "macros": [...]
  },
  "selected_items": ["cpuUtilization", "memoryUtilization", ...],
  "selected_traps": ["linkDown", ...],
  "discovery_rules": [...],
  "trigger_overrides": {...}
}

Response:
{
  "status": "success",
  "template_json": {...},
  "filename": "20250109_143022 Cisco Catalyst 9300 Template.json",
  "validation": {
    "errors": [],
    "warnings": [...],
    "info": [...]
  }
}
```

#### 3. Configuration Save/Load
```
POST /api/config/save
GET /api/config/load/{config_id}
```

#### 4. Validation
```
POST /api/validate
Content-Type: application/json

Request: Same as /generate

Response:
{
  "status": "success",
  "validation": {
    "template_structure": "valid",
    "oid_validation": "valid",
    "trigger_expressions": "valid",
    "errors": [],
    "warnings": [
      "ifPhysAddress has no trigger (informational field)",
      "Large table split into 3 discovery rules"
    ],
    "info": [
      "6 value mappings auto-generated from enum syntax"
    ]
  }
}
```

### Frontend Architecture

#### Technology Stack
- **Framework**: React (recommended) or Vue.js
- **State Management**: React Context API or Redux (for complex state)
- **UI Components**:
  - Material-UI or Ant Design (pre-built components)
  - react-beautiful-dnd (drag-and-drop)
  - AG-Grid or TanStack Table (large data tables)
  - react-json-view (JSON preview)
- **Form Handling**: React Hook Form + Yup validation
- **HTTP Client**: Axios
- **Styling**: CSS Modules or Styled Components

#### Component Structure
```
src/
├── components/
│   ├── Layout/
│   │   ├── Sidebar.jsx
│   │   ├── TopNav.jsx
│   │   └── StepContainer.jsx
│   ├── Steps/
│   │   ├── Step1Upload.jsx
│   │   ├── Step2Configure.jsx
│   │   ├── Step3Items.jsx
│   │   ├── Step4Discovery.jsx
│   │   ├── Step5Triggers.jsx
│   │   └── Step6Review.jsx
│   ├── Common/
│   │   ├── FileUpload.jsx
│   │   ├── ItemSelector.jsx
│   │   ├── TriggerEditor.jsx
│   │   └── ValidationMessages.jsx
│   └── Preview/
│       ├── JsonViewer.jsx
│       └── SummaryStats.jsx
├── api/
│   └── templateApi.js
├── contexts/
│   └── TemplateContext.jsx
├── hooks/
│   ├── useFileUpload.js
│   └── useTemplateGeneration.js
└── App.jsx
```

#### State Management
```javascript
// TemplateContext.jsx
const TemplateContext = createContext();

const TemplateProvider = ({ children }) => {
  const [state, setState] = useState({
    currentStep: 1,
    sessionId: null,
    mibData: [],
    templateInfo: {},
    selectedItems: [],
    selectedTraps: [],
    discoveryRules: [],
    triggerOverrides: {},
    validationResults: {}
  });

  return (
    <TemplateContext.Provider value={{ state, setState }}>
      {children}
    </TemplateContext.Provider>
  );
};
```

### Session Management
- Use browser localStorage for draft saving
- Session ID from backend for multi-step workflow
- Auto-save every 30 seconds
- "Resume from saved draft" on landing page

### File Handling Flow
```
User uploads CSV
    ↓
Frontend sends to /api/upload
    ↓
Backend: Save to temp file
    ↓
MIBValidator.extract_from_uploaded_file(file_stream)
    ↓
Returns: MIB data + stats + discovered tables
    ↓
Frontend: Store in state, show in Step 1
    ↓
User configures through steps 2-5
    ↓
Frontend sends config to /api/generate
    ↓
Backend: Create Template object (existing code)
    ↓
Returns: Generated JSON + validation
    ↓
Frontend: Display preview, allow download
```

---

## Implementation Plan

### Phase 1: Backend API (Estimated: 3-5 days)

#### Tasks
1. **Create API layer** (api.py)
   - Flask setup with CORS
   - File upload endpoint
   - Template generation endpoint
   - Validation endpoint
   - Error handling

2. **Modify file handling** (mib_validator.py)
   - Add `extract_from_uploaded_file()` method
   - Support file streams instead of paths
   - Test with in-memory file objects

3. **Add response serialization**
   - JSON serialization for all Zabbix objects
   - Error formatting for API responses
   - Validation result formatting

4. **Testing**
   - Unit tests for API endpoints
   - Test file upload with various CSV formats
   - Test error handling scenarios

#### Deliverables
- Working REST API
- API documentation
- Postman collection for testing

### Phase 2: Frontend Development (Estimated: 2-3 weeks)

#### Week 1: Core Structure
1. **Project setup**
   - Create React app
   - Install dependencies
   - Setup routing and state management

2. **Layout components**
   - Sidebar navigation
   - Top navigation bar
   - Step container
   - Progress tracking

3. **Step 1: File Upload**
   - Drag-and-drop component
   - File upload to API
   - Data preview table
   - Column mapping interface

4. **Step 2: Configuration Form**
   - Template info form
   - Macro management
   - Form validation

#### Week 2: Core Functionality
1. **Step 3: Item Selection**
   - Two-panel layout
   - Search and filter
   - Item selection logic
   - Selected items display

2. **Step 4: Discovery Rules**
   - Discovery rule cards
   - Item prototype selection
   - Expandable details
   - Include/exclude toggles

3. **API integration**
   - Connect all steps to backend
   - State management
   - Error handling

#### Week 3: Advanced Features & Polish
1. **Step 5: Trigger Customization**
   - Trigger list display
   - Inline editing
   - Advanced mode

2. **Step 6: Review & Generate**
   - Summary display
   - JSON preview
   - Validation results
   - Download functionality

3. **Additional Features**
   - Save/load drafts
   - Export configuration
   - Help system
   - Dark mode

4. **Testing & Refinement**
   - User flow testing
   - Bug fixes
   - Performance optimization
   - Responsive design testing

#### Deliverables
- Fully functional web interface
- User documentation
- Deployment-ready build

### Phase 3: Docker Integration (Estimated: 2-3 days)

#### Tasks
1. **Create Dockerfile**
   - Multi-stage build
   - Python backend + static frontend
   - Optimize image size

2. **Docker Compose**
   - Single container setup
   - Volume mounting for uploads
   - Environment configuration

3. **Testing**
   - Build and run container
   - Test all functionality
   - Performance verification

4. **Documentation**
   - Docker deployment guide
   - Configuration options
   - Troubleshooting

#### Deliverables
- Production-ready Docker image
- Docker Compose configuration
- Deployment documentation

---

## Deployment

### Docker Container

#### Dockerfile
```dockerfile
# Multi-stage build

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask flask-cors gunicorn

# Copy Python code
COPY . .

# Copy frontend build
COPY --from=frontend-build /frontend/build /app/static

# Create uploads directory
RUN mkdir -p /app/uploads /app/created_templates

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "api:app"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  zabbix-template-generator:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./created_templates:/app/created_templates
    environment:
      - FLASK_ENV=production
      - MAX_UPLOAD_SIZE=50MB
    restart: unless-stopped
```

#### Usage
```bash
# Build and run
docker-compose up -d

# Access at http://localhost:5000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables
```bash
# .env file
FLASK_ENV=production
MAX_UPLOAD_SIZE=50MB
SESSION_TIMEOUT=3600
DEBUG=false
CORS_ORIGINS=*
```

### Volume Mounts
- `/app/uploads`: Temporary uploaded files
- `/app/created_templates`: Generated templates
- Optional: `/app/config`: Custom configuration files

### Resource Requirements
- CPU: 1 core minimum, 2 recommended
- RAM: 512MB minimum, 1GB recommended
- Disk: 1GB for application + space for uploads/templates

### Security Considerations
- File upload size limits
- File type validation (CSV/XLSX only)
- Temporary file cleanup
- CORS configuration for production
- No external API calls (offline capable)

---

## Future Enhancements

### MVP Focus
Initial release includes:
- ✅ CSV/XLSX file upload
- ✅ Step-by-step wizard
- ✅ Item/trap selection
- ✅ Discovery rule preview
- ✅ Basic trigger customization
- ✅ JSON download

### Post-MVP Features
- Advanced trigger expression editor
- Graph prototype configuration
- Batch processing (multiple MIB files)
- Template comparison tool
- Import existing template for editing
- Custom trigger pattern definitions
- Value mapping editor
- Collaborative features (share configs)

---

## Success Metrics

### User Experience
- ✅ Upload to download in < 5 minutes
- ✅ No manual Excel editing required
- ✅ Clear validation messages
- ✅ Intuitive navigation

### Technical
- ✅ < 2 second page load time
- ✅ API response < 1 second for typical MIB
- ✅ Support MIBs up to 10,000 entries
- ✅ Docker image < 500MB

### Quality
- ✅ Same output quality as CLI tool
- ✅ All existing tests pass
- ✅ No data loss during workflow
- ✅ Graceful error handling

---

## Appendix

### References
- Zabbix 7.0 Template Format: https://www.zabbix.com/documentation/7.0/manual/xml_export_import/templates
- Flask Documentation: https://flask.palletsprojects.com/
- React Documentation: https://react.dev/

### Open Questions
- [ ] Authentication/multi-user support needed?
- [ ] Database for storing templates/history?
- [ ] API rate limiting?
- [ ] Template library/sharing features?

### Change Log
- 2025-01-09: Initial specification created
- Tags section removed from UI design
- Docker deployment confirmed
- Minimal refactoring approach validated
