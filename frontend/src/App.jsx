import React from 'react'
import { Box } from '@mui/material'
import { TemplateProvider, useTemplate } from './contexts/TemplateContext'
import Sidebar from './components/Layout/Sidebar'
import TopNav from './components/Layout/TopNav'
import StepContainer from './components/Layout/StepContainer'

// Import step components
import Step1Upload from './components/Steps/Step1Upload'
import Step2Configure from './components/Steps/Step2Configure'
import Step3Items from './components/Steps/Step3Items'
import Step4Discovery from './components/Steps/Step4Discovery'
import Step5Triggers from './components/Steps/Step5Triggers'
import Step6Review from './components/Steps/Step6Review'

function AppContent() {
  const { state } = useTemplate()

  const renderStep = () => {
    switch (state.currentStep) {
      case 1:
        return <Step1Upload />
      case 2:
        return <Step2Configure />
      case 3:
        return <Step3Items />
      case 4:
        return <Step4Discovery />
      case 5:
        return <Step5Triggers />
      case 6:
        return <Step6Review />
      default:
        return <Step1Upload />
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <TopNav />
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            backgroundColor: '#f5f5f5',
          }}
        >
          <StepContainer>{renderStep()}</StepContainer>
        </Box>
      </Box>
    </Box>
  )
}

function App() {
  return (
    <TemplateProvider>
      <AppContent />
    </TemplateProvider>
  )
}

export default App
