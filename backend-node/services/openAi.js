// Main OpenAI Logic

import OpenAI from "openai"
import config from "../config"

const openai = new OpenAI({
    apiKey: config.openai.apiKey
})

export const getSummary = async (transcriptText) => {
    try {
        const response = await openai.chat.completions.create({
            model: 'gpt-3.5-turbo',
            messages: [
                {
                    role: 'system',
                    content: 'You are a helpful assistant that summarizes transcripts. Provide a main topic, '
                }
            ]
        })
    } catch (err) {
        console.err('Error getting sumamry from OpenAi:', err.response?.data || err.message)
        throw new Error('Failed to generate summary with OpenAI')
    }
}