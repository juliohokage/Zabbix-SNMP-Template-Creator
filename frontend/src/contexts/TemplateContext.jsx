import React, { createContext, useContext, useState, useCallback } from 'react'

const TemplateContext = createContext()

export const useTemplate = () => {
  const context = useContext(TemplateContext)
  if (!context) {
    throw new Error('useTemplate must be used within TemplateProvider')
  }
  return context
}

export const TemplateProvider = ({ children }) => {
  const [state, setState] = useState({
    // Navigation
    currentStep: 1,
    completedSteps: [],

    // Session
    sessionId: null,
    filename: null,

    // Data from upload
    mibData: [],
    snmpItemsAvailable: [],
    snmpTrapsAvailable: [],
    discoveredTables: [],
    stats: {},

    // Configuration (Step 2)
    templateInfo: {
      name: '',
      group: '',
      device: '',
      manufacturer: '',
      model: '',
      macros: []
    },

    // Selection (Step 3)
    selectedItems: [],
    selectedTraps: [],

    // Discovery Rules (Step 4)
    selectedDiscoveryRules: [],
    discoveryRuleConfig: {},

    // Triggers (Step 5)
    triggerOverrides: {},

    // Results (Step 6)
    generatedTemplate: null,
    validationResults: null,
  })

  const updateState = useCallback((updates) => {
    setState((prev) => ({ ...prev, ...updates }))
  }, [])

  const setCurrentStep = useCallback((step) => {
    setState((prev) => ({
      ...prev,
      currentStep: step,
      completedSteps: [...new Set([...prev.completedSteps, prev.currentStep])]
    }))
  }, [])

  const nextStep = useCallback(() => {
    setState((prev) => {
      const newStep = Math.min(prev.currentStep + 1, 6)
      return {
        ...prev,
        currentStep: newStep,
        completedSteps: [...new Set([...prev.completedSteps, prev.currentStep])]
      }
    })
  }, [])

  const previousStep = useCallback(() => {
    setState((prev) => ({
      ...prev,
      currentStep: Math.max(prev.currentStep - 1, 1)
    }))
  }, [])

  const resetState = useCallback(() => {
    setState({
      currentStep: 1,
      completedSteps: [],
      sessionId: null,
      filename: null,
      mibData: [],
      snmpItemsAvailable: [],
      snmpTrapsAvailable: [],
      discoveredTables: [],
      stats: {},
      templateInfo: {
        name: '',
        group: '',
        device: '',
        manufacturer: '',
        model: '',
        macros: []
      },
      selectedItems: [],
      selectedTraps: [],
      selectedDiscoveryRules: [],
      discoveryRuleConfig: {},
      triggerOverrides: {},
      generatedTemplate: null,
      validationResults: null,
    })
  }, [])

  const loadState = useCallback((loadedState) => {
    setState(loadedState)
  }, [])

  const value = {
    state,
    updateState,
    setCurrentStep,
    nextStep,
    previousStep,
    resetState,
    loadState
  }

  return (
    <TemplateContext.Provider value={value}>
      {children}
    </TemplateContext.Provider>
  )
}
