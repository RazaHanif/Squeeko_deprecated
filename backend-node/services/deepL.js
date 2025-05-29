// Main DeepL logic

import axios from 'axios'
import config from '../config'

// DeepL has free & paid endpoints
// Using the free one for now for testing

const API_BASE_URL = 'https://api-free.deepl.com/v2'
const PAID_API_BASE_URL = 'https://api.deepl.com/v2'

export const translateText = async (text, targetLang='en') => {
    try {
        const response = await axios.post(
            `${API_BASE_URL}/translate`,
            null,
            {
                params: {
                    auth_key: config.deepl.apiKey,
                    text: text,
                    target_lang: targetLang.toUpperCase()
                }
            }
        )
        return response.data.translations[0].text
    } catch (err) {
        console.error('Error translating text with DeepL:', err.response?.data || err.message)
        throw new Error('Failed translating text with DeepL')
    }
}