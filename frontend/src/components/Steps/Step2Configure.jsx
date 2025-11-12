import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  IconButton,
  Grid,
  Divider
} from '@mui/material'
import { Add, Delete } from '@mui/icons-material'
import { useTemplate } from '../../contexts/TemplateContext'

export default function Step2Configure() {
  const { state, updateState, nextStep, previousStep } = useTemplate()
  const [formData, setFormData] = useState({
    name: '',
    group: '',
    device: '',
    manufacturer: '',
    model: '',
    macros: []
  })

  useEffect(() => {
    // Initialize with template info from session if available
    if (state.templateInfo) {
      setFormData({
        name: state.templateInfo.Template || state.templateInfo.name || '',
        group: state.templateInfo.Group || state.templateInfo.group || '',
        device: state.templateInfo.Device || state.templateInfo.device || '',
        manufacturer: state.templateInfo.Manufacturer || state.templateInfo.manufacturer || '',
        model: state.templateInfo.Model || state.templateInfo.model || '',
        macros: parseMacros(state.templateInfo.Macros || state.templateInfo.macros || [])
      })
    }
  }, [state.templateInfo])

  const parseMacros = (macrosInput) => {
    if (Array.isArray(macrosInput)) {
      return macrosInput.map(m => ({
        name: m.name || m.Macro || '',
        value: m.value || m.Value || ''
      }))
    }
    return []
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleMacroChange = (index, field, value) => {
    const newMacros = [...formData.macros]
    newMacros[index][field] = value
    setFormData(prev => ({
      ...prev,
      macros: newMacros
    }))
  }

  const handleAddMacro = () => {
    setFormData(prev => ({
      ...prev,
      macros: [...prev.macros, { name: '', value: '' }]
    }))
  }

  const handleRemoveMacro = (index) => {
    const newMacros = formData.macros.filter((_, i) => i !== index)
    setFormData(prev => ({
      ...prev,
      macros: newMacros
    }))
  }

  const handleNext = () => {
    // Update context with form data
    updateState({
      templateInfo: {
        ...state.templateInfo,
        name: formData.name,
        group: formData.group,
        device: formData.device,
        manufacturer: formData.manufacturer,
        model: formData.model,
        macros: formData.macros
      }
    })
    nextStep()
  }

  const isValid = () => {
    return formData.name.trim() !== '' && formData.group.trim() !== ''
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Step 2: Template Configuration
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure the basic information for your Zabbix template.
      </Typography>

      {/* Basic Information */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Basic Information
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              required
              label="Template Name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              helperText="Enter a descriptive name for your template"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              required
              label="Template Group"
              value={formData.group}
              onChange={(e) => handleInputChange('group', e.target.value)}
              placeholder="Templates/Network Devices/Cisco"
              helperText="Group path in Zabbix (e.g., Templates/Network Devices/...)"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Device Type"
              value={formData.device}
              onChange={(e) => handleInputChange('device', e.target.value)}
              placeholder="Switch, Router, Server, etc."
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Manufacturer"
              value={formData.manufacturer}
              onChange={(e) => handleInputChange('manufacturer', e.target.value)}
              placeholder="Cisco, Juniper, HP, etc."
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Model"
              value={formData.model}
              onChange={(e) => handleInputChange('model', e.target.value)}
              placeholder="Catalyst 9300, MX Series, etc."
            />
          </Grid>
        </Grid>
      </Paper>

      {/* SNMP Macros */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            SNMP Macros
          </Typography>
          <Button
            startIcon={<Add />}
            onClick={handleAddMacro}
            variant="outlined"
            size="small"
          >
            Add Macro
          </Button>
        </Box>

        {formData.macros.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            No macros defined. Click "Add Macro" to add SNMP community strings and other parameters.
          </Typography>
        ) : (
          <Box>
            {formData.macros.map((macro, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={5}>
                    <TextField
                      fullWidth
                      label="Macro Name"
                      value={macro.name}
                      onChange={(e) => handleMacroChange(index, 'name', e.target.value)}
                      placeholder="{$SNMP_COMMUNITY}"
                      size="small"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Value"
                      value={macro.value}
                      onChange={(e) => handleMacroChange(index, 'value', e.target.value)}
                      placeholder="public"
                      size="small"
                    />
                  </Grid>
                  <Grid item xs={1}>
                    <IconButton
                      onClick={() => handleRemoveMacro(index)}
                      color="error"
                      size="small"
                    >
                      <Delete />
                    </IconButton>
                  </Grid>
                </Grid>
              </Box>
            ))}
          </Box>
        )}
      </Paper>

      {/* Default Macros Suggestion */}
      <Paper sx={{ p: 2, mb: 3, backgroundColor: '#f5f5f5' }}>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          <strong>Common SNMP Macros:</strong>
        </Typography>
        <Typography variant="caption" color="text.secondary">
          • {'{$SNMP_COMMUNITY}'} = public<br />
          • {'{$SNMP_PORT}'} = 161<br />
          • {'{$IFINDEX.MATCHES}'} = .*<br />
          • {'{$CPU.MAX}'} = 90<br />
          • {'{$MEMORY.MAX}'} = 90
        </Typography>
      </Paper>

      {/* Navigation */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
        <Button
          variant="outlined"
          size="large"
          onClick={previousStep}
        >
          Back
        </Button>
        <Button
          variant="contained"
          size="large"
          onClick={handleNext}
          disabled={!isValid()}
        >
          Next: Select Items
        </Button>
      </Box>
    </Box>
  )
}
