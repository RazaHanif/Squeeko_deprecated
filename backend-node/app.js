// Main bakend server file

// Basic Imports
require('dotenv').config()
const express = require('express')
const app = express()

const port = process.env.PORT || 3000


// Middleware
app.use(express.json())

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