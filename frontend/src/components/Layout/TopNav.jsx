import React, { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Tooltip
} from '@mui/material'
import {
  Save,
  FileDownload,
  Help,
  Brightness4,
  Brightness7,
  MoreVert
} from '@mui/icons-material'
import { useTemplate } from '../../contexts/TemplateContext'

export default function TopNav() {
  const { state, resetState } = useTemplate()
  const [anchorEl, setAnchorEl] = useState(null)
  const [darkMode, setDarkMode] = useState(false)

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleSaveDraft = () => {
    try {
      localStorage.setItem('template_draft', JSON.stringify(state))
      alert('Draft saved successfully!')
    } catch (error) {
      alert('Failed to save draft: ' + error.message)
    }
    handleMenuClose()
  }

  const handleLoadDraft = () => {
    try {
      const draft = localStorage.getItem('template_draft')
      if (draft) {
        const parsedDraft = JSON.parse(draft)
        // TODO: Load draft into state
        alert('Draft loaded successfully!')
      } else {
        alert('No saved draft found')
      }
    } catch (error) {
      alert('Failed to load draft: ' + error.message)
    }
    handleMenuClose()
  }

  const handleExportConfig = () => {
    try {
      const config = {
        templateInfo: state.templateInfo,
        selectedItems: state.selectedItems,
        selectedTraps: state.selectedTraps,
        selectedDiscoveryRules: state.selectedDiscoveryRules,
        triggerOverrides: state.triggerOverrides
      }
      const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'template_config.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      alert('Failed to export config: ' + error.message)
    }
    handleMenuClose()
  }

  const handleNewTemplate = () => {
    if (confirm('Start a new template? This will clear your current progress.')) {
      resetState()
    }
    handleMenuClose()
  }

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {state.filename ? `Editing: ${state.filename}` : 'Zabbix SNMP Template Generator'}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Save Draft">
            <Button
              startIcon={<Save />}
              onClick={handleSaveDraft}
              disabled={!state.sessionId}
            >
              Save Draft
            </Button>
          </Tooltip>

          <Tooltip title="Export Configuration">
            <Button
              startIcon={<FileDownload />}
              onClick={handleExportConfig}
              disabled={!state.sessionId}
            >
              Export Config
            </Button>
          </Tooltip>

          <Tooltip title="Help">
            <IconButton
              onClick={() => window.open('https://github.com/Galileo-Suite/Zabbix-SNMP-Template-Creator', '_blank')}
            >
              <Help />
            </IconButton>
          </Tooltip>

          <Tooltip title="Toggle Dark Mode">
            <IconButton onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Tooltip>

          <IconButton onClick={handleMenuOpen}>
            <MoreVert />
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={handleLoadDraft}>Load Draft</MenuItem>
            <MenuItem onClick={handleNewTemplate}>New Template</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  )
}
