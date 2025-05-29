// Main AssemblyAI logic

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
        
    } catch (err) {
        
    }
}