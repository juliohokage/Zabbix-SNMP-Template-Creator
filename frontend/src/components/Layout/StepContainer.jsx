import React from 'react'
import { Box, Container, Paper } from '@mui/material'

export default function StepContainer({ children }) {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Paper elevation={2} sx={{ p: 4, minHeight: '70vh' }}>
        {children}
      </Paper>
    </Container>
  )
}
