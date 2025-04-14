// Main bakend server file

// Basic Imports
require('dotenv').config()
const express = require('express')
const app = express()


// Middleware
app.use(express.json())

// Routes

app.get('/', (req, res) => {
    res.status(200).json({
        message: 'Hello, Squeeko!'
    })
})

const port = process.env.PORT || 3000