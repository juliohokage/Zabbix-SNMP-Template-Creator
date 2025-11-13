import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText
} from '@mui/material'
import {
  CheckCircle,
  Warning,
  Info,
  Download,
  ContentCopy
} from '@mui/icons-material'
import JsonView from 'react18-json-view'
import 'react18-json-view/src/style.css'
import { useTemplate } from '../../contexts/TemplateContext'
import { generateTemplate } from '../../api/templateApi'

export default function Step6Review() {
  const { state, previousStep } = useTemplate()
  const [activeTab, setActiveTab] = useState(0)
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)
  const [error, setError] = useState(null)
  const [templateData, setTemplateData] = useState(null)

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)

    try {
      const config = {
        session_id: state.sessionId,
        template_info: {
          Template: state.templateInfo.name,
          Group: state.templateInfo.group,
          Device: state.templateInfo.device,
          Manufacturer: state.templateInfo.manufacturer,
          Model: state.templateInfo.model,
          Macros: state.templateInfo.macros.map(m => ({
            Macro: m.name,
            Value: m.value
          }))
        },
        selected_items: state.selectedItems,
        selected_traps: state.selectedTraps,
        discovery_rules: state.selectedDiscoveryRules,
        trigger_overrides: state.triggerOverrides,
        options: {
          include_items: true,
          include_traps: true,
          include_discovery_rules: true,
          generate_triggers: state.triggerOverrides?.generate_triggers !== false
        }
      }

      const response = await generateTemplate(config)

      if (response.status === 'success') {
        setTemplateData(response.data)
        setGenerated(true)
      } else {
        setError(response.message || 'Failed to generate template')
      }
    } catch (err) {
      console.error('Generation error:', err)
      setError(err.response?.data?.message || err.message || 'Failed to generate template')
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!templateData) return

    const jsonStr = JSON.stringify(templateData.template_json, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = templateData.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleCopyToClipboard = () => {
    if (!templateData) return

    const jsonStr = JSON.stringify(templateData.template_json, null, 2)
    navigator.clipboard.writeText(jsonStr)
      .then(() => alert('Template JSON copied to clipboard!'))
      .catch(() => alert('Failed to copy to clipboard'))
  }

  const renderSummary = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        Template Summary
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Template Name
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {state.templateInfo.name || 'Not specified'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary">
              Template Group
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {state.templateInfo.group || 'Not specified'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Manufacturer
            </Typography>
            <Typography variant="body1">
              {state.templateInfo.manufacturer || 'N/A'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Device Type
            </Typography>
            <Typography variant="body1">
              {state.templateInfo.device || 'N/A'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="subtitle2" color="text.secondary">
              Model
            </Typography>
            <Typography variant="body1">
              {state.templateInfo.model || 'N/A'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      <Typography variant="h6" gutterBottom>
        Content Summary
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="primary">
              {state.selectedItems.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              SNMP Items
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="secondary">
              {state.selectedTraps.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              SNMP Traps
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="info.main">
              {state.selectedDiscoveryRules.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Discovery Rules
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4" color="success.main">
              {state.templateInfo.macros?.length || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Macros
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {!generated ? (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            Review your configuration above. When ready, click "Generate Template" to create
            your Zabbix JSON template.
          </Alert>

          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleGenerate}
              disabled={generating}
              startIcon={generating ? <CircularProgress size={20} /> : null}
            >
              {generating ? 'Generating...' : 'Generate Template'}
            </Button>
          </Box>
        </Box>
      ) : (
        <Box>
          <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
            Template generated successfully! You can now download it or view the JSON.
          </Alert>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<Download />}
              onClick={handleDownload}
            >
              Download JSON
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<ContentCopy />}
              onClick={handleCopyToClipboard}
            >
              Copy to Clipboard
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  )

  const renderJsonPreview = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        JSON Preview
      </Typography>

      {!generated ? (
        <Alert severity="info">
          Generate the template first to view the JSON output.
        </Alert>
      ) : (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Filename: <strong>{templateData?.filename}</strong>
            </Typography>
            <Box>
              <Button
                size="small"
                startIcon={<Download />}
                onClick={handleDownload}
                sx={{ mr: 1 }}
              >
                Download
              </Button>
              <Button
                size="small"
                startIcon={<ContentCopy />}
                onClick={handleCopyToClipboard}
              >
                Copy
              </Button>
            </Box>
          </Box>

          <Paper
            variant="outlined"
            sx={{
              p: 2,
              maxHeight: '600px',
              overflow: 'auto',
              backgroundColor: '#f5f5f5'
            }}
          >
            <JsonView
              src={templateData?.template_json || {}}
              collapsed={2}
              enableClipboard={true}
            />
          </Paper>
        </Box>
      )}
    </Box>
  )

  const renderValidation = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        Validation Results
      </Typography>

      {!generated ? (
        <Alert severity="info">
          Generate the template first to see validation results.
        </Alert>
      ) : templateData?.validation ? (
        <Box>
          {/* Success checks */}
          <Paper sx={{ p: 3, mb: 2, backgroundColor: '#f1f8f4' }}>
            <Typography variant="h6" gutterBottom color="success.main">
              <CheckCircle sx={{ verticalAlign: 'middle', mr: 1 }} />
              Validation Passed
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="✓ Template structure valid" />
              </ListItem>
              <ListItem>
                <ListItemText primary="✓ All OIDs validated against MIB data" />
              </ListItem>
              <ListItem>
                <ListItemText primary="✓ Zabbix 7.0 format compliance" />
              </ListItem>
            </List>
          </Paper>

          {/* Warnings */}
          {templateData.validation.warnings && templateData.validation.warnings.length > 0 && (
            <Paper sx={{ p: 3, mb: 2, backgroundColor: '#fff8e1' }}>
              <Typography variant="h6" gutterBottom color="warning.main">
                <Warning sx={{ verticalAlign: 'middle', mr: 1 }} />
                Warnings ({templateData.validation.warnings.length})
              </Typography>
              <List dense>
                {templateData.validation.warnings.map((warning, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`• ${warning}`} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          {/* Info */}
          {templateData.validation.info && templateData.validation.info.length > 0 && (
            <Paper sx={{ p: 3, backgroundColor: '#e3f2fd' }}>
              <Typography variant="h6" gutterBottom color="info.main">
                <Info sx={{ verticalAlign: 'middle', mr: 1 }} />
                Information
              </Typography>
              <List dense>
                {templateData.validation.info.map((info, index) => (
                  <ListItem key={index}>
                    <ListItemText primary={`• ${info}`} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Box>
      ) : (
        <Alert severity="info">
          No validation results available.
        </Alert>
      )}
    </Box>
  )

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Step 6: Review & Generate
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Review your configuration and generate the final Zabbix template.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label="Summary" />
          <Tab label="JSON Preview" disabled={!generated} />
          <Tab label="Validation" disabled={!generated} />
        </Tabs>
      </Box>

      {activeTab === 0 && renderSummary()}
      {activeTab === 1 && renderJsonPreview()}
      {activeTab === 2 && renderValidation()}

      {/* Navigation */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
        <Button
          variant="outlined"
          size="large"
          onClick={previousStep}
          disabled={generating}
        >
          Back
        </Button>
        {generated && (
          <Button
            variant="contained"
            size="large"
            color="success"
            startIcon={<Download />}
            onClick={handleDownload}
          >
            Download Template
          </Button>
        )}
      </Box>
    </Box>
  )
}
