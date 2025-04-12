
// All boilerplate stuff
require('dotenv').config()
const express = require('express')
const cors = require('cors')
const app = express()
const port = process.env.PORT || 3000
const { OpenAI } = require('openai')

// Open ai LLM configuration

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
})
// Idk which model to use yet this is whats recommended
// const llmModel = 'gpt-3.5-turbo'

// Middleware
app.use(cors())
app.use(express.json())

// API Routes
// Will move all this to route & comp files later just doing this to get started

// Summary Route
// Input: Transcript text
// Output: Text Summary
app.post('/api/summarize', async (req, res) => {
    const { transcript } = req.body

    if (!transcript) {
        return res.status(400).json({
            error: 'Transcript text is required'
        })
    }

    console.log(`Transcript received: ${transcript.length()}`)

    // Call to chatgpt
    try {
        const completion = await openai.chat.completions.create({
            model: llmModel,
            messages: [
                { role: 'system', content: 'You are a helpful assistant that summarizes texts.'},
                { role: 'user', content: `Please summarize the following transcript : \n\n ${transcript}`}
            ],
            max_tokens: 150, // Adjust max token for summary length
            temperature: 0.5, // Adjust as needed - lower = more deteministic | higher = more creative
        })

        const summary = completion.choices[0]?.message?.content?.trim()

        if (!summary) {
            throw new Error('LLM did not return a valid sumamry')
        }

        console.log('Summary Generated!')

        // TODO: Save transcript & Summary to DB 
        // Ideally save on user device locally

        res.json({ summary })
    } catch (err) {
        console.error('Error Calling LLM', err)
        res.status(500).json({ error: 'Failed to generate summary', details: err.message })
        
    }
})

// Chat Route
// Input: User Message 
// Output: GPT Response
app.post('/api/chat', async (req, res) => {
    const { summary, userMessage, chatHistory = [] } = req.body

    if (!summary || !userMessage) {
        return res.status(400).json({ 
            error: 'Summary context and/or User Message are requried'
        })
    }

    console.log(`Received chat message: "${userMessage}" with summary context`)

    // Basic history formatting (adjsut based on gpt requirements)

    const messages = [
        { role: 'system', content: `You are a helpful assistant. Answer the user's questions based *only* on the provided summary context. Do not use any external knowledge. Here is the summary: \n\n ${summary}` },
        // Add previous chatHistory here to implement multi-turn chat
        { role: 'user', content: userMessage }
    ]

    try {
        const completion = await openai.chat.completions.create({
            model: llmModel,
            messages: messages,
            max_tokens: 100, // Adjsut as needed
            temperature: 0.7, // Adjsut as needed
        })
        const chatResponse = completion.choices[0]?.message?.content?.trim()

        if (!chatResponse) {
            throw new Error('LLM did not return a valid chat response')
        }

        console.log('Chat response generated')

        // TODO: Save transcript & Summary to DB 
        // Ideally save on user device locally

        res.json({ response: chatResponse })
        
    } catch (err) {
        console.error('Error calling LLM for Chat', err)
        res.status(500).json({
            error: 'Failed to get chat response',
            details: err.message
        })
    }
})

// Basic root route
app.get('/', (req, res) => {
    res.send('Squeeko Backend is running!')
})

// Start server
app.listen(port, () => {
    console.log(`Server is live on port: ${ port }`)
})