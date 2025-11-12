import React, { useState, useMemo } from 'react'
import {
  Box,
  Typography,
  Button,
  TextField,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Checkbox,
  Chip,
  Tabs,
  Tab,
  InputAdornment,
  FormControlLabel
} from '@mui/material'
import { Search, Speed, Notifications } from '@mui/icons-material'
import { useTemplate } from '../../contexts/TemplateContext'

export default function Step3Items() {
  const { state, updateState, nextStep, previousStep } = useTemplate()
  const [activeTab, setActiveTab] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedItems, setSelectedItems] = useState(state.selectedItems || [])
  const [selectedTraps, setSelectedTraps] = useState(state.selectedTraps || [])
  const [selectAllItems, setSelectAllItems] = useState(false)
  const [selectAllTraps, setSelectAllTraps] = useState(false)

  // Filter items based on search
  const filteredItems = useMemo(() => {
    if (!searchQuery) return state.snmpItemsAvailable || []
    const query = searchQuery.toLowerCase()
    return (state.snmpItemsAvailable || []).filter(item =>
      (item.Name && item.Name.toLowerCase().includes(query)) ||
      (item.OID && item.OID.toLowerCase().includes(query)) ||
      (item.Description && item.Description.toLowerCase().includes(query))
    )
  }, [state.snmpItemsAvailable, searchQuery])

  const filteredTraps = useMemo(() => {
    if (!searchQuery) return state.snmpTrapsAvailable || []
    const query = searchQuery.toLowerCase()
    return (state.snmpTrapsAvailable || []).filter(trap =>
      (trap.Name && trap.Name.toLowerCase().includes(query)) ||
      (trap.OID && trap.OID.toLowerCase().includes(query))
    )
  }, [state.snmpTrapsAvailable, searchQuery])

  const handleToggleItem = (item) => {
    const itemName = item.Name
    setSelectedItems(prev =>
      prev.includes(itemName)
        ? prev.filter(name => name !== itemName)
        : [...prev, itemName]
    )
  }

  const handleToggleTrap = (trap) => {
    const trapName = trap.Name
    setSelectedTraps(prev =>
      prev.includes(trapName)
        ? prev.filter(name => name !== trapName)
        : [...prev, trapName]
    )
  }

  const handleSelectAllItems = () => {
    if (selectAllItems) {
      setSelectedItems([])
    } else {
      setSelectedItems(filteredItems.map(item => item.Name))
    }
    setSelectAllItems(!selectAllItems)
  }

  const handleSelectAllTraps = () => {
    if (selectAllTraps) {
      setSelectedTraps([])
    } else {
      setSelectedTraps(filteredTraps.map(trap => trap.Name))
    }
    setSelectAllTraps(!selectAllTraps)
  }

  const handleNext = () => {
    updateState({
      selectedItems,
      selectedTraps
    })
    nextStep()
  }

  const getValueTypeChip = (type) => {
    if (!type) return null
    const typeStr = String(type).toLowerCase()

    if (typeStr.includes('int') || typeStr.includes('gauge') || typeStr.includes('counter')) {
      return <Chip label="Numeric" size="small" color="primary" />
    }
    if (typeStr.includes('string') || typeStr.includes('octet')) {
      return <Chip label="Text" size="small" color="secondary" />
    }
    if (typeStr.includes('timeticks')) {
      return <Chip label="Time" size="small" color="info" />
    }
    return <Chip label={type} size="small" />
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Step 3: Select Items & Traps
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Choose which SNMP items and traps to include in your template.
      </Typography>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab
            label={`SNMP Items (${selectedItems.length}/${(state.snmpItemsAvailable || []).length})`}
            icon={<Speed />}
            iconPosition="start"
          />
          <Tab
            label={`SNMP Traps (${selectedTraps.length}/${(state.snmpTrapsAvailable || []).length})`}
            icon={<Notifications />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Search Bar */}
      <TextField
        fullWidth
        placeholder="Search by name, OID, or description..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
      />

      {/* Items Tab */}
      {activeTab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={selectAllItems}
                  onChange={handleSelectAllItems}
                />
              }
              label={`Select All (${filteredItems.length} items)`}
            />
            <Typography variant="body2" color="text.secondary">
              {selectedItems.length} items selected
            </Typography>
          </Box>

          <Paper variant="outlined" sx={{ maxHeight: '500px', overflow: 'auto' }}>
            <List dense>
              {filteredItems.length === 0 ? (
                <ListItem>
                  <ListItemText
                    primary="No items available"
                    secondary="Upload a file with SNMP items to get started"
                  />
                </ListItem>
              ) : (
                filteredItems.map((item, index) => (
                  <ListItem
                    key={index}
                    secondaryAction={getValueTypeChip(item.Type)}
                    disablePadding
                  >
                    <ListItemButton onClick={() => handleToggleItem(item)}>
                      <ListItemIcon>
                        <Checkbox
                          edge="start"
                          checked={selectedItems.includes(item.Name)}
                          tabIndex={-1}
                          disableRipple
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.Name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.secondary">
                              OID: {item.OID}
                            </Typography>
                            {item.Description && (
                              <>
                                <br />
                                <Typography component="span" variant="caption" color="text.secondary">
                                  {item.Description.substring(0, 100)}
                                  {item.Description.length > 100 ? '...' : ''}
                                </Typography>
                              </>
                            )}
                          </>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))
              )}
            </List>
          </Paper>
        </Box>
      )}

      {/* Traps Tab */}
      {activeTab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={selectAllTraps}
                  onChange={handleSelectAllTraps}
                />
              }
              label={`Select All (${filteredTraps.length} traps)`}
            />
            <Typography variant="body2" color="text.secondary">
              {selectedTraps.length} traps selected
            </Typography>
          </Box>

          <Paper variant="outlined" sx={{ maxHeight: '500px', overflow: 'auto' }}>
            <List dense>
              {filteredTraps.length === 0 ? (
                <ListItem>
                  <ListItemText
                    primary="No traps available"
                    secondary="Upload a file with SNMP traps to get started"
                  />
                </ListItem>
              ) : (
                filteredTraps.map((trap, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemButton onClick={() => handleToggleTrap(trap)}>
                      <ListItemIcon>
                        <Checkbox
                          edge="start"
                          checked={selectedTraps.includes(trap.Name)}
                          tabIndex={-1}
                          disableRipple
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={trap.Name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.secondary">
                              OID: {trap.OID}
                            </Typography>
                            {trap.Description && (
                              <>
                                <br />
                                <Typography component="span" variant="caption" color="text.secondary">
                                  {trap.Description.substring(0, 100)}
                                  {trap.Description.length > 100 ? '...' : ''}
                                </Typography>
                              </>
                            )}
                          </>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))
              )}
            </List>
          </Paper>
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
          Next: Discovery Rules
        </Button>
      </Box>
    </Box>
  )
}
