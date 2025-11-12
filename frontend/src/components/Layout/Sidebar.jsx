import React from 'react'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider
} from '@mui/material'
import {
  CloudUpload,
  Settings,
  ListAlt,
  Explore,
  NotificationsActive,
  Preview,
  CheckCircle,
  RadioButtonUnchecked,
  PlayArrow
} from '@mui/icons-material'
import { useTemplate } from '../../contexts/TemplateContext'

const drawerWidth = 280

const steps = [
  { number: 1, title: 'Upload', icon: CloudUpload },
  { number: 2, title: 'Configure', icon: Settings },
  { number: 3, title: 'Items & Traps', icon: ListAlt },
  { number: 4, title: 'Discovery Rules', icon: Explore },
  { number: 5, title: 'Triggers', icon: NotificationsActive },
  { number: 6, title: 'Review & Generate', icon: Preview },
]

export default function Sidebar() {
  const { state, setCurrentStep } = useTemplate()

  const getStepStatus = (stepNumber) => {
    if (stepNumber === state.currentStep) return 'active'
    if (state.completedSteps.includes(stepNumber)) return 'completed'
    return 'pending'
  }

  const getStepIcon = (stepNumber, IconComponent) => {
    const status = getStepStatus(stepNumber)
    if (status === 'completed') return <CheckCircle color="success" />
    if (status === 'active') return <PlayArrow color="primary" />
    return <IconComponent color="disabled" />
  }

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          backgroundColor: '#fafafa',
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Typography variant="h5" fontWeight="bold" color="primary" gutterBottom>
          Zabbix SNMP
        </Typography>
        <Typography variant="h6" fontWeight="bold" color="text.secondary">
          Template Generator
        </Typography>
      </Box>

      <Divider />

      <List sx={{ pt: 2 }}>
        {steps.map((step) => {
          const status = getStepStatus(step.number)
          const isClickable = state.completedSteps.includes(step.number) || step.number === state.currentStep

          return (
            <ListItem key={step.number} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                selected={status === 'active'}
                onClick={() => isClickable && setCurrentStep(step.number)}
                disabled={!isClickable}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(212, 0, 0, 0.08)',
                    '&:hover': {
                      backgroundColor: 'rgba(212, 0, 0, 0.12)',
                    },
                  },
                }}
              >
                <ListItemIcon>
                  {getStepIcon(step.number, step.icon)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      fontWeight={status === 'active' ? 'bold' : 'normal'}
                      color={status === 'pending' ? 'text.disabled' : 'text.primary'}
                    >
                      {step.number}. {step.title}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          )
        })}
      </List>

      <Box sx={{ flexGrow: 1 }} />

      {state.sessionId && (
        <Box sx={{ p: 2, backgroundColor: '#f0f0f0', m: 2, borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Session Active
          </Typography>
          <Typography variant="body2" fontWeight="bold" noWrap>
            {state.filename || 'Unknown'}
          </Typography>
        </Box>
      )}
    </Drawer>
  )
}
