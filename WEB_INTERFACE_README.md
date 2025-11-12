# Zabbix SNMP Template Generator - Web Interface

A user-friendly web interface for generating Zabbix SNMP templates from MIB Browser exports.

## Features

- **Drag-and-Drop File Upload**: Easy file upload with visual feedback
- **Step-by-Step Wizard**: Guided process through 6 intuitive steps
- **Interactive Selection**: Choose which items, traps, and discovery rules to include
- **Real-Time Validation**: Instant feedback on configuration
- **JSON Preview**: View and download generated templates
- **Auto-Generated Triggers**: Smart trigger generation based on item types
- **Docker Support**: One-command deployment

## Quick Start

### Option 1: Docker (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Access the web interface:**
   Open your browser to [http://localhost:5000](http://localhost:5000)

3. **Stop the service:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

1. **Install Backend Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

3. **Start the Backend (Terminal 1):**
   ```bash
   python api.py
   ```

4. **Start the Frontend (Terminal 2):**
   ```bash
   cd frontend
   npm run dev
   ```

5. **Access the interface:**
   Open [http://localhost:3000](http://localhost:3000)

## Usage Guide

### Step 1: Upload MIB Data

1. Drag and drop your MIB Browser export file (Excel or CSV)
2. Or click "Browse Files" to select a file
3. Wait for processing to complete
4. Review the upload summary

**Supported formats:** .xlsx, .xls, .csv (max 50MB)

### Step 2: Configure Template

Fill in the basic template information:

- **Template Name** (required): Descriptive name for your template
- **Template Group** (required): Zabbix group path (e.g., `Templates/Network Devices/Cisco`)
- **Device Type**: Switch, Router, Server, etc.
- **Manufacturer**: Cisco, Juniper, HP, etc.
- **Model**: Specific model number

**Add SNMP Macros:**
- Click "Add Macro" to define SNMP parameters
- Common macros: `{$SNMP_COMMUNITY}`, `{$CPU.MAX}`, `{$MEMORY.MAX}`

### Step 3: Select Items & Traps

**SNMP Items Tab:**
- Browse available SNMP items from your MIB
- Use search to filter by name, OID, or description
- Check items to include in your template
- View item types (Numeric, Text, Time)

**SNMP Traps Tab:**
- Select SNMP traps to monitor
- Same search and filter functionality

**Tip:** Use "Select All" to include all items, then deselect what you don't need.

### Step 4: Discovery Rules

- Review auto-detected discovery rules (SNMP tables)
- Check/uncheck rules to include/exclude
- View details about each rule (item count, split status)
- Split tables are automatically handled for large MIBs

**What's included:**
- Master SNMP walk item
- Item prototypes for each table column
- Auto-generated trigger prototypes

### Step 5: Trigger Configuration

- Toggle automatic trigger generation on/off
- Review examples of auto-generated triggers
- Triggers are created for:
  - Status changes (interface up/down)
  - Utilization metrics (CPU, memory)
  - Error counters
  - State changes

**Note:** Triggers can be customized after importing into Zabbix.

### Step 6: Review & Generate

**Summary Tab:**
- Review all configuration
- See counts of items, traps, discovery rules, and macros
- Click "Generate Template" to create JSON

**JSON Preview Tab:**
- View formatted JSON output
- Copy to clipboard or download
- Syntax highlighting for easy reading

**Validation Tab:**
- See validation results
- Review warnings and informational messages
- Ensure template compliance with Zabbix 7.0

**Download:**
- Click "Download JSON" to save the template
- File will be named with timestamp and template name
- Import directly into Zabbix

## API Endpoints

The web interface uses a REST API backend:

### Health Check
```
GET /api/health
```

### Upload File
```
POST /api/upload
Content-Type: multipart/form-data

Returns: Session ID and parsed MIB data
```

### Generate Template
```
POST /api/generate
Content-Type: application/json

Body: {
  "session_id": "...",
  "template_info": {...},
  "selected_items": [...],
  "selected_traps": [...],
  "discovery_rules": [...],
  "options": {...}
}

Returns: Generated template JSON
```

### Validate Configuration
```
POST /api/validate
Content-Type: application/json

Returns: Validation results
```

### Session Management
```
GET /api/session/{session_id}
DELETE /api/session/{session_id}
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Flask Configuration
FLASK_ENV=production
MAX_UPLOAD_SIZE=52428800  # 50MB
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO

# CORS Settings
CORS_ORIGINS=*  # Change for production
```

### Docker Volumes

The Docker setup includes two persistent volumes:

- `./uploads`: Temporary uploaded files
- `./created_templates`: Generated templates

## Architecture

### Backend (Python/Flask)

- **api.py**: REST API endpoints
- **utils/**: Core processing logic (unchanged from CLI)
- **zabbix_objects/**: Template generation classes

### Frontend (React)

- **Layout Components**: Sidebar navigation, top bar
- **Step Components**: 6-step wizard interface
- **Context**: Global state management
- **API Client**: Axios-based API integration

### Multi-Stage Docker Build

1. **Stage 1**: Build React frontend with Node.js
2. **Stage 2**: Python backend with Flask + static frontend
3. **Result**: Single container serving both frontend and API

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Edit docker-compose.yml to change port
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

### File Upload Fails

Check file size limits:

```bash
# In docker-compose.yml or .env
MAX_UPLOAD_SIZE=104857600  # Increase to 100MB
```

### CORS Errors

For production deployment:

```bash
# Set specific origins in .env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Session Lost

Sessions are stored in memory. Restarting the container clears sessions:

1. Download your template before stopping
2. Or implement Redis for persistent sessions (future enhancement)

## Development

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run in debug mode
python api.py

# Run tests
pytest tests/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (hot reload)
npm run dev

# Build for production
npm run build
```

### Building Docker Image

```bash
# Build
docker build -t zabbix-template-generator .

# Run
docker run -p 5000:5000 zabbix-template-generator
```

## Production Deployment

### Security Recommendations

1. **Set specific CORS origins:**
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **Use HTTPS:** Deploy behind a reverse proxy (nginx, Caddy)

3. **File size limits:** Adjust based on your needs

4. **Session management:** Consider Redis for production

5. **Authentication:** Add auth layer for multi-user environments

### Reverse Proxy Example (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # File upload size
        client_max_body_size 50M;
    }
}
```

## Known Limitations

1. **Session Storage**: In-memory sessions (cleared on restart)
2. **Single File Upload**: One file at a time
3. **Advanced Trigger Editing**: Not yet available in UI (coming soon)
4. **Batch Processing**: Not yet supported
5. **Template Comparison**: Future feature

## Roadmap

- [ ] Persistent session storage (Redis)
- [ ] Advanced trigger expression editor
- [ ] Graph prototype configuration
- [ ] Batch processing for multiple MIB files
- [ ] Template comparison and merge tools
- [ ] User authentication and multi-tenancy
- [ ] Template library and sharing
- [ ] Export to different Zabbix versions

## Support

- **Documentation**: See main [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/Galileo-Suite/Zabbix-SNMP-Template-Creator/issues)
- **CLI Usage**: Run `python main.py --help`

## License

Same as the main project - see [LICENSE](LICENSE) file.
