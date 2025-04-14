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

// Idk if this is the right setup for this, will need to check later
const port = process.env.PORT || 3000

// Server
const start = async () => {
    try {
        app.listen(port, () => {
            console.log(`Squeeko Server is live on port: ${port}`);            
        })
    } catch (err) {
        console.log(err);
        
    }
}


start()