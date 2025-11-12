import React, { useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material'
import { Info } from '@mui/icons-material'
import { useTemplate } from '../../contexts/TemplateContext'

export default function Step5Triggers() {
  const { state, updateState, nextStep, previousStep } = useTemplate()
  const [generateTriggers, setGenerateTriggers] = useState(true)

  const handleNext = () => {
    updateState({
      triggerOverrides: {
        ...state.triggerOverrides,
        generate_triggers: generateTriggers
      }
    })
    nextStep()
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Step 5: Trigger Configuration
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure automatic trigger generation for your template.
      </Typography>

      {/* Auto-generation Toggle */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <FormControlLabel
          control={
            <Switch
              checked={generateTriggers}
              onChange={(e) => setGenerateTriggers(e.target.checked)}
              color="primary"
            />
          }
          label={
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                Enable Automatic Trigger Generation
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Automatically create triggers based on SNMP item types and values
              </Typography>
            </Box>
          }
        />
      </Paper>

      {/* Information about auto-generated triggers */}
      {generateTriggers && (
        <Alert severity="info" icon={<Info />} sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            <strong>Automatic triggers will be created for:</strong>
          </Typography>
          <Typography variant="body2" component="div">
            • <strong>Status items:</strong> Triggers when operational status changes<br />
            • <strong>Utilization metrics:</strong> Triggers when CPU/Memory exceeds thresholds<br />
            • <strong>Error counters:</strong> Triggers when error rates are abnormal<br />
            • <strong>State changes:</strong> Triggers for up/down interface states
          </Typography>
        </Alert>
      )}

      {/* Trigger Examples */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Example Auto-Generated Triggers
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            CPU Utilization High
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            Expression: min(/Template/cpu.util,5m) {'>'} {'{$CPU.MAX}'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Severity: High | Threshold: 90%
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Interface Down
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            Expression: count(...ifOperStatus,#3,"ne","1"){'>='}2
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Severity: Average | Detects interface operational status changes
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box>
          <Typography variant="subtitle2" color="primary" gutterBottom>
            Memory Utilization High
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            Expression: min(/Template/mem.util,5m) {'>'} {'{$MEMORY.MAX}'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Severity: High | Threshold: 90%
          </Typography>
        </Box>
      </Paper>

      {/* Advanced Options Info */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: '#f5f5f5' }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Note:</strong> You can customize trigger expressions, severities, and thresholds
          after importing the template into Zabbix. The auto-generated triggers provide a solid
          starting point based on industry best practices.
        </Typography>
      </Paper>

      {/* Future Enhancement Notice */}
      <Alert severity="warning" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Advanced trigger customization</strong> (editing individual trigger expressions
          and thresholds in the UI) will be available in a future update. For now, you can disable
          auto-generation and add custom triggers manually in Zabbix after import.
        </Typography>
      </Alert>

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
        >
          Next: Review & Generate
        </Button>
      </Box>
    </Box>
  )
}
