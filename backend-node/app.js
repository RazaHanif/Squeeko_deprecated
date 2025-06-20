import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'


require('dotenv').config()
import config from './config'


import authRoutes from './routes/auth'
import jobRoutes from './routes/job'


import { errorHandler } from './middleware/error'
import { authHandler } from './middleware/auth'

const express = require('express')
const app = express()


// Middleware
app.use(express.json())
app.use(cors())
app.use(helmet())
app.use(morgan('dev'))

// Routes
app.use('/api/auth', authRoutes)
app.use('/api/jobs', jobRoutes)
// More will be added...i think

// AssemblyAI Webhook
// Cannot be behind any auth middleware
app.post('/api/webhooks/assemblyai', (req, res, next) => {
    // TODO: Implement webhook verification (AssemblyAI provides a signiture)
    console.log('AssemblyAI Webhook Received: ', req.body)

    res.status(200).send('OK')
})


app.use(errorHandler)

app.get('/', (req, res) => {
    res.status(200).json({
        message: 'Hello, Squeeko!'
    })
})


// Server
const port = process.env.PORT || 3000

const start = async () => {
    try {
        app.listen(port, () => {
            console.log(`Squeeko.js Server is live on port: ${port}`);            
        })
    } catch (err) {
        console.log(err);
    }
}


start()

