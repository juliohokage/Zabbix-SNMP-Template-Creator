import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
  FormControlLabel,
  Checkbox,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider
} from '@mui/material'
import {
  ExpandMore,
  Analytics,
  Code,
  NotificationImportant
} from '@mui/icons-material'
import { previewCSV, processCSV } from '../api/templateApi'

export default function CSVPreprocessDialog({ open, onClose, file, onSuccess }) {
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [error, setError] = useState(null)

  // Configuration state
  const [config, setConfig] = useState({
    template_name: 'SNMP Template',
    template_group: 'Templates/Network Devices',
    manufacturer: 'Generic',
    device: 'Network Device',
    model: '',
    macros: '{$SNMP_COMMUNITY}=public',
    tags: '',
    include_informational: true
  })

  // Load preview when dialog opens
  useEffect(() => {
    if (open && file) {
      loadPreview()
    }
  }, [open, file])

  const loadPreview = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await previewCSV(file)

      if (response.status === 'success') {
        setPreviewData(response.data)

        // Auto-populate template name from MIB module if available
        if (response.data.primary_mib_module) {
          setConfig(prev => ({
            ...prev,
            template_name: `${response.data.primary_mib_module} Template`
          }))
        }
      } else {
        setError(response.message || 'Failed to preview CSV')
      }
    } catch (err) {
      console.error('Preview error:', err)
      setError(err.response?.data?.message || err.message || 'Failed to preview CSV file')
    } finally {
      setLoading(false)
    }
  }

  const handleProcess = async () => {
    setProcessing(true)
    setError(null)

    try {
      const response = await processCSV(file, config)

      if (response.status === 'success') {
        onSuccess(response.data, file.name)
        onClose()
      } else {
        setError(response.message || 'Failed to process CSV')
      }
    } catch (err) {
      console.error('Processing error:', err)
      setError(err.response?.data?.message || err.message || 'Failed to process CSV file')
    } finally {
      setProcessing(false)
    }
  }

  const handleConfigChange = (field) => (event) => {
    setConfig({
      ...config,
      [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value
    })
  }

  return (
    <Dialog
      open={open}
      onClose={processing ? undefined : onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        CSV Preprocessing - {file?.name}
      </DialogTitle>

      <DialogContent dividers>
        {loading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography>Analyzing CSV file...</Typography>
          </Box>
        ) : error && !previewData ? (
          <Alert severity="error">{error}</Alert>
        ) : previewData ? (
          <Box>
            {/* Statistics Summary */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Analytics /> MIB Data Analysis
              </Typography>

              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
                <Chip
                  label={`${previewData.mib_entries} Total Entries`}
                  color="default"
                  variant="outlined"
                />
                <Chip
                  label={`${previewData.statistics.readable_items} Readable Items`}
                  color="primary"
                />
                <Chip
                  label={`${previewData.statistics.traps} Traps`}
                  color="warning"
                />
                <Chip
                  label={`${previewData.statistics.tables} Tables`}
                  color="secondary"
                />
              </Box>

              {/* Categorized counts */}
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Auto-suggested items by priority:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                  <Chip
                    label={`🔴 Critical: ${previewData.categorized_counts.critical}`}
                    size="small"
                    color="error"
                  />
                  <Chip
                    label={`🟡 Important: ${previewData.categorized_counts.important}`}
                    size="small"
                    color="warning"
                  />
                  <Chip
                    label={`🔵 Informational: ${previewData.categorized_counts.informational}`}
                    size="small"
                    color="info"
                  />
                </Box>
              </Box>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Configuration Form */}
            <Typography variant="h6" gutterBottom>
              Template Configuration
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Template Name"
                value={config.template_name}
                onChange={handleConfigChange('template_name')}
                required
                fullWidth
              />

              <TextField
                label="Template Group"
                value={config.template_group}
                onChange={handleConfigChange('template_group')}
                fullWidth
                helperText="E.g., Templates/Network Devices/Cisco"
              />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Manufacturer"
                  value={config.manufacturer}
                  onChange={handleConfigChange('manufacturer')}
                  fullWidth
                />

                <TextField
                  label="Device Type"
                  value={config.device}
                  onChange={handleConfigChange('device')}
                  fullWidth
                />
              </Box>

              <TextField
                label="Model (Optional)"
                value={config.model}
                onChange={handleConfigChange('model')}
                fullWidth
              />

              {/* Advanced Settings Accordion */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>Advanced Settings</Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Macros"
                    value={config.macros}
                    onChange={handleConfigChange('macros')}
                    fullWidth
                    helperText="E.g., {$SNMP_COMMUNITY}=public"
                  />

                  <TextField
                    label="Tags"
                    value={config.tags}
                    onChange={handleConfigChange('tags')}
                    fullWidth
                    helperText="Comma-separated, e.g., vendor:cisco,class:networking"
                  />

                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={config.include_informational}
                        onChange={handleConfigChange('include_informational')}
                      />
                    }
                    label="Include informational items (serial numbers, descriptions)"
                  />
                </AccordionDetails>
              </Accordion>

              {/* Suggested Items Preview */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Code fontSize="small" />
                    Suggested SNMP Items ({previewData.suggested_items_count})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {previewData.suggested_items?.slice(0, 20).map((item, idx) => (
                      <Chip key={idx} label={item} size="small" variant="outlined" />
                    ))}
                    {previewData.suggested_items?.length > 20 && (
                      <Chip label={`+${previewData.suggested_items.length - 20} more`} size="small" />
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <NotificationImportant fontSize="small" />
                    Suggested SNMP Traps ({previewData.suggested_traps_count})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {previewData.suggested_traps?.map((trap, idx) => (
                      <Chip key={idx} label={trap} size="small" variant="outlined" color="warning" />
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        ) : null}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={processing}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleProcess}
          disabled={loading || processing || !previewData}
          startIcon={processing && <CircularProgress size={20} />}
        >
          {processing ? 'Processing...' : 'Process & Continue'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
