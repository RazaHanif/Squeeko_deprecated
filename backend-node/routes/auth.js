// API Routing for auth

import express from 'express'
import * as auth from '../controllers/auth'

const router = express.Router()

router.post('/register', auth.register)
router.post('/login', auth.login)

// refresh-token
// logout
// forgot-password

export default router
