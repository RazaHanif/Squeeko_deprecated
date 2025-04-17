import OpenAI from 'openai/index.mjs'
const openai = new OpenAI({
    apiKey: process.env.TEST_API_KEY
})

const model = 'gpt-4o-mini'

// Test route to OPENAI api, wont work cuz the TEST_API_KEY is wrong
const sumamrize = async (req, res) => {
    const {
        user: { userId },
        params: { transcript },
    } = req

    if (!userId) {
        // Send error
        // Also check if user has access to this feature
    }

    if (!transcript) {
        // Do something
    }

    if (transcript.length > 100 ) {
        // Have a max length (based on tokens)
        // Maybe split up the text into chunks or send back error
    }

    // Send text off for summary
    // Learn prompting and create a good tailored prompt
    const completion = await openai.chat.completions.create({
        model: model,
        messages: [{
            'role': 'user',
            'content': `Create summary using only following text: ${ transcript }`,
        }]
    })

    // Send back only the content from response? Check and tailor later on
    res.status(200).json(completion.choices[0].message.content)
}

module.exports = {
  sumamrize,
}
