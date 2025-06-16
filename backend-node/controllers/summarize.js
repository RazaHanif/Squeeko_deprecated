import OpenAI from 'openai/index.mjs'
const openai = new OpenAI({
    apiKey: process.env.TEST_API_KEY
})

const model = 'gpt-4o-mini'

// Test route to OPENAI api, wont work cuz the TEST_API_KEY is wrong
// Check if user has permission
// max_length (based on tokens) - if bigger, split into chunks
// Copy paste prompt from python mistral logic
