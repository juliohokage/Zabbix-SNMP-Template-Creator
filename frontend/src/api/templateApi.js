import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Upload and parse Excel/CSV file
 * @param {File} file - The file to upload
 * @returns {Promise} Response with session data
 */
export const uploadFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

/**
 * Generate Zabbix template JSON
 * @param {Object} config - Template configuration
 * @returns {Promise} Response with generated template
 */
export const generateTemplate = async (config) => {
  const response = await api.post('/generate', config)
  return response.data
}

/**
 * Validate configuration
 * @param {Object} config - Template configuration
 * @returns {Promise} Response with validation results
 */
export const validateConfiguration = async (config) => {
  const response = await api.post('/validate', config)
  return response.data
}

/**
 * Get session data
 * @param {string} sessionId - Session ID
 * @returns {Promise} Response with session data
 */
export const getSession = async (sessionId) => {
  const response = await api.get(`/session/${sessionId}`)
  return response.data
}

/**
 * Delete session
 * @param {string} sessionId - Session ID
 * @returns {Promise} Response
 */
export const deleteSession = async (sessionId) => {
  const response = await api.delete(`/session/${sessionId}`)
  return response.data
}

/**
 * Health check
 * @returns {Promise} Response with health status
 */
export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

/**
 * Preview CSV file and get suggestions
 * @param {File} file - The CSV file to preview
 * @returns {Promise} Response with preview data and suggestions
 */
export const previewCSV = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`${API_BASE_URL}/csv/preview`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

/**
 * Process CSV file with configuration
 * @param {File} file - The CSV file to process
 * @param {Object} config - Processing configuration
 * @returns {Promise} Response with session data (same as uploadFile)
 */
export const processCSV = async (file, config) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('template_name', config.template_name || 'SNMP Template')
  formData.append('template_group', config.template_group || 'Templates/Network Devices')
  formData.append('manufacturer', config.manufacturer || 'Generic')
  formData.append('device', config.device || 'Network Device')
  formData.append('model', config.model || '')
  formData.append('macros', config.macros || '{$SNMP_COMMUNITY}=public')
  formData.append('tags', config.tags || '')
  formData.append('include_informational', config.include_informational !== false ? 'true' : 'false')

  if (config.selected_items) {
    formData.append('selected_items', JSON.stringify(config.selected_items))
  }

  if (config.selected_traps) {
    formData.append('selected_traps', JSON.stringify(config.selected_traps))
  }

  const response = await axios.post(`${API_BASE_URL}/csv/process`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export default api
