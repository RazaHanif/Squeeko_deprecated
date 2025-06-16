import axios from 'axios'
import config from '../config'

const API_BASE_URL = 'https://api.assemblyai.com/v2'

export const startTranscription = async (audioUrl, webhookUrl) => {
    try {
        const response = await axios.post(
            `${API_BASE_URL}/transcript`, 
            {
                audio_url: audioUrl,
                speaker_labels: true,
                webhook_url: webhookUrl,
                audio_language_detection: true
            },
            {
                headers: {
                    'Authorization': config.assemblyAI.apiKey,
                    'Content-Type': 'application/json'
                }
            }
        )
        return response.data
    } catch (err) {
        console.error('Error starting AssembleyAI transcription:', err.response?.data || err.message)
        throw new Error('Error starting AssembleyAI transcription')
    }
}

export const getTranscriptionResult = async (assemblyAiJobId) => {
    try {
        const response = await axios.get(
            `${API_BASE_URL}/transcript/${assemblyAiJobId}`,
            {
                headers: {
                    'Authorization': config.assemblyAI.apiKey,
                }
            }
        )
        return response.data
    } catch (err) {
        console.error('Error fetching AssembleyAI transcription:', err.response?.data || err.message)
        throw new Error('Error fetching AssembleyAI transcription')
    }
}

// TODO: Implement webhook verification here or in middleware
// AssemblyAI sends a signature in the header
// Need to verify it to ensure the webhook is legit
