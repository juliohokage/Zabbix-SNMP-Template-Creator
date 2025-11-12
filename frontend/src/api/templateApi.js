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

export default api
