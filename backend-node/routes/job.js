// API route for jobs

import express from 'express'
import * as jobs from '../controllers/job'
import { authenticateToken } from '../middleware/auth'

const router = express.Router()

