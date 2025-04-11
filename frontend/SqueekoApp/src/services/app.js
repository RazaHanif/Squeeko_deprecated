// IDK if i will use axios or if i use something else

import axios from 'axios'

// IMPORTANT: IDK whats going on here idk if i need this.
const API_BASE_URL = 'http://127.0.0.1:3000/api'

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    }
})

export const summarizeText = async (transcript) => {
    try {
        const response = await apiClient.post('/summarize', { transcript })
        return response.data
    } catch (err) {
        console.error('API Error (summarizeText)', err.response?.data || err.message)
        throw err
    }
}

export const chatWithSummary = async (summary, userMessage, chatHistory = []) => {
    try {
        const response = await apiClient.post('/chat', { summary, userMessage, chatHistory })
        return response.data
    } catch (err) {
        console.error('API Error (chatWithSummary)', err.response?.data || err.message)
        throw err
    }
}
