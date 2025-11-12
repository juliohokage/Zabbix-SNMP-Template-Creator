import React, { useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  FormControlLabel,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemText
} from '@mui/material'
import { ExpandMore, TableChart, Warning } from '@mui/icons-material'
import { useTemplate } from '../../contexts/TemplateContext'

export default function Step4Discovery() {
  const { state, updateState, nextStep, previousStep } = useTemplate()
  const [selectedRules, setSelectedRules] = useState(
    state.selectedDiscoveryRules.length > 0
      ? state.selectedDiscoveryRules
      : (state.discoveredTables || []).map(t => t.oid)
  )

  const handleToggleRule = (oid) => {
    setSelectedRules(prev =>
      prev.includes(oid)
        ? prev.filter(o => o !== oid)
        : [...prev, oid]
    )
  }

  const handleSelectAll = () => {
    if (selectedRules.length === (state.discoveredTables || []).length) {
      setSelectedRules([])
    } else {
      setSelectedRules((state.discoveredTables || []).map(t => t.oid))
    }
  }

  const handleNext = () => {
    updateState({
      selectedDiscoveryRules: selectedRules
    })
    nextStep()
  }

  const discoveredTables = state.discoveredTables || []
  const splitTables = discoveredTables.filter(t => t.is_split)

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Step 4: Discovery Rules
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure which discovery rules (SNMP tables) to include in your template.
      </Typography>

      {splitTables.length > 0 && (
        <Alert severity="warning" icon={<Warning />} sx={{ mb: 3 }}>
          {splitTables.length} large table(s) have been automatically split into multiple sub-discovery rules
          to stay within Zabbix SNMP walk limits.
        </Alert>
      )}

      {/* Summary */}
      <Paper sx={{ p: 2, mb: 3, backgroundColor: '#f5f5f5' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body1">
            <strong>{discoveredTables.length}</strong> discovery rules detected
          </Typography>
          <Box>
            <Chip
              label={`${selectedRules.length} selected`}
              color="primary"
              size="small"
              sx={{ mr: 1 }}
            />
            <Button
              variant="outlined"
              size="small"
              onClick={handleSelectAll}
            >
              {selectedRules.length === discoveredTables.length ? 'Deselect All' : 'Select All'}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Discovery Rules List */}
      {discoveredTables.length === 0 ? (
        <Alert severity="info">
          No discovery rules found. This is normal if your MIB doesn't contain table structures.
        </Alert>
      ) : (
        <Box>
          {discoveredTables.map((table, index) => (
            <Accordion key={index} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', pr: 2 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRules.includes(table.oid)}
                        onChange={() => handleToggleRule(table.oid)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    }
                    label=""
                    sx={{ mr: 2 }}
                  />
                  <TableChart sx={{ mr: 2, color: 'primary.main' }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {table.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      OID: {table.oid}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label={`${table.item_count} items`}
                      size="small"
                      color="info"
                    />
                    {table.is_split && (
                      <Chip
                        label="Split Table"
                        size="small"
                        color="warning"
                      />
                    )}
                  </Box>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ pl: 7 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Details:</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    This discovery rule will create {table.item_count} item prototypes.
                    Item prototypes are automatically created for each row in the SNMP table.
                  </Typography>

                  {table.is_split && (
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        This table was too large for a single SNMP walk operation and has been split
                        into multiple sub-rules. Each sub-rule will include the index OIDs plus a subset
                        of metric OIDs.
                      </Typography>
                    </Alert>
                  )}

                  <Typography variant="body2" gutterBottom>
                    <strong>What will be created:</strong>
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText
                        primary="1 Master SNMP Walk Item"
                        secondary="Performs the SNMP table walk to discover rows"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary={`${table.item_count} Item Prototypes`}
                        secondary="One for each column in the SNMP table"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Auto-generated Triggers"
                        secondary="Triggers will be created based on item types and values"
                      />
                    </ListItem>
                  </List>
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

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
          Next: Triggers
        </Button>
      </Box>
    </Box>
  )
}
