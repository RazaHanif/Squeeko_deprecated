// Node Backend


// Basic Imports
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'


// Import Config
require('dotenv').config()
import config from './config'


// Import Routes
import authRoutes from './routes/auth'
import jobRoutes from './routes/job'


// Import Middleware
import { errorHandler } from './middleware/error'
import { authHandler } from './middleware/auth'

const express = require('express')
const app = express()


// Just for testing
const port = process.env.PORT || 3000


// Middleware
app.use(express.json())
app.use(cors())
app.use(helmet())
app.use(morgan('dev'))

// Routes
app.use('/api/auth', authRoutes)
app.use('/api/jobs', jobRoutes)

// Routes
const summaryRouter = require('./routes/summarize')

app.use('/api/summarize', summaryRouter);

app.get('/', (req, res) => {
    res.status(200).json({
        message: 'Hello, Squeeko!'
    })
})

// Server
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