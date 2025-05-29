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
            temperature: 0.2,
            messages: [
                {
                    role: 'system',
                    content: "You are a helpful assistant that always responds in a valid JSON format using exactly the structure and keys provided by the user."
                },
                {
                    role: 'user',
                    content: `Analyze the following meeting transcript. 
Identify the main topic, provide a concise summary, extract key discussion points, and list any tasks or action items.

Return your response as a **valid JSON object** with this structure:

{
    "mainTopic": "A concise, overarching topic of the discussion.",
    "summary": "A brief summary of the entire conversation, highlighting the most important themes and outcomes.",
    "keyPoints": ["Bullet point 1", "Bullet point 2", "..."],
    "tasks": ["Task description, including responsible person if mentioned or implied"]
}

Transcript:
---
${transcriptText}
---

Make sure:
- The JSON is valid and parsable.
- The 'tasks' field includes names (if available) or speaker labels (like 'Speaker 1') when responsibility is implied.
- If no tasks are mentioned, return an empty array for "tasks".
`
                }
            ]
        })
    } catch (err) {
        console.err('Error getting sumamry from OpenAi:', err.response?.data || err.message)
        throw new Error('Failed to generate summary with OpenAI')
    }
}