import express from 'express'
import * as jobs from '../controllers/job'
import { authenticateToken } from '../middleware/auth'

const router = express.Router()

// All routes are protected
router.use(authenticateToken)

router.post('/', jobs.createJob)
router.get('/:id', jobs.getJobStatus)

// Get users jobs
// Delete jobs

export default router