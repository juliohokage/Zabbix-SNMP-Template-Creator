import React, { useState, useCallback } from 'react'
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip
} from '@mui/material'
import { CloudUpload, CheckCircle } from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { uploadFile } from '../../api/templateApi'
import { useTemplate } from '../../contexts/TemplateContext'

export default function Step1Upload() {
  const { updateState, nextStep } = useTemplate()
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [uploadedData, setUploadedData] = useState(null)

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    setUploading(true)
    setError(null)

    try {
      const response = await uploadFile(file)

      if (response.status === 'success') {
        const data = response.data

        // Update context
        updateState({
          sessionId: data.session_id,
          filename: file.name,
          snmpItemsAvailable: data.snmp_items_available,
          snmpTrapsAvailable: data.snmp_traps_available,
          discoveredTables: data.discovered_tables,
          stats: data.stats,
          templateInfo: {
            ...data.template_info,
            macros: data.template_info.Macros || []
          }
        })

        setUploadedData(data)
        setUploadSuccess(true)
      } else {
        setError(response.message || 'Upload failed')
      }
    } catch (err) {
      console.error('Upload error:', err)
      setError(err.response?.data?.message || err.message || 'Failed to upload file')
    } finally {
      setUploading(false)
    }
  }, [updateState])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    multiple: false,
    disabled: uploading
  })

  const handleNext = () => {
    if (uploadSuccess) {
      nextStep()
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Step 1: Upload MIB Data
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload your MIB Browser export file (Excel or CSV format) to begin creating your Zabbix template.
      </Typography>

      {/* Upload Area */}
      <Box sx={{ my: 4 }}>
        <Paper
          {...getRootProps()}
          elevation={isDragActive ? 4 : 1}
          sx={{
            p: 6,
            textAlign: 'center',
            cursor: uploading ? 'not-allowed' : 'pointer',
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.3s ease',
            '&:hover': {
              borderColor: uploading ? 'grey.300' : 'primary.main',
              backgroundColor: uploading ? 'background.paper' : 'action.hover',
            },
          }}
        >
          <input {...getInputProps()} />

          {uploading ? (
            <Box>
              <CircularProgress size={60} sx={{ mb: 2 }} />
              <Typography variant="h6">Uploading and processing...</Typography>
            </Box>
          ) : uploadSuccess ? (
            <Box>
              <CheckCircle color="success" sx={{ fontSize: 60, mb: 2 }} />
              <Typography variant="h6" color="success.main">
                File uploaded successfully!
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {uploadedData?.stats.total_entries} MIB entries loaded
              </Typography>
            </Box>
          ) : (
            <Box>
              <CloudUpload sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop your file here' : 'Drag & drop your MIB file here'}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                or
              </Typography>
              <Button variant="contained" sx={{ mt: 2 }}>
                Browse Files
              </Button>
              <Typography variant="caption" display="block" sx={{ mt: 2 }} color="text.secondary">
                Supported formats: .xlsx, .xls, .csv (Max 50MB)
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Upload Statistics */}
      {uploadSuccess && uploadedData && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Upload Summary
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              label={`${uploadedData.stats.total_entries} Total MIB Entries`}
              color="primary"
              variant="outlined"
            />
            <Chip
              label={`${uploadedData.stats.tables_detected} Discovery Rules`}
              color="secondary"
              variant="outlined"
            />
            <Chip
              label={`${uploadedData.stats.items_count} SNMP Items`}
              color="info"
              variant="outlined"
            />
            <Chip
              label={`${uploadedData.stats.traps_count} SNMP Traps`}
              color="warning"
              variant="outlined"
            />
          </Box>

          {/* Discovered Tables Preview */}
          {uploadedData.discovered_tables.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Discovered Tables (Preview)
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>OID</TableCell>
                      <TableCell align="right">Item Count</TableCell>
                      <TableCell align="center">Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {uploadedData.discovered_tables.slice(0, 10).map((table, index) => (
                      <TableRow key={index}>
                        <TableCell>{table.name}</TableCell>
                        <TableCell>{table.oid}</TableCell>
                        <TableCell align="right">{table.item_count}</TableCell>
                        <TableCell align="center">
                          {table.is_split ? (
                            <Chip label="Split" size="small" color="warning" />
                          ) : (
                            <Chip label="Standard" size="small" color="success" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {uploadedData.discovered_tables.length > 10 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Showing 10 of {uploadedData.discovered_tables.length} tables
                </Typography>
              )}
            </Box>
          )}
        </Box>
      )}

      {/* Navigation */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleNext}
          disabled={!uploadSuccess}
        >
          Next: Configure Template
        </Button>
      </Box>
    </Box>
  )
}
