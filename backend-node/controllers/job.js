// Request handler for Job routes
import * as jobService from '../services/job'
import * as fileUpload from '../utils/fileUpload'

export const createJob = async (req, res, next) => {
    try {
        const userId = req.user.userId
        // TODO: Validate input (originalFilename, ensure audio type)
        // Generate presigned URL for direct client-to-cloud upload
        // Frontend will use this URL to upload the actual audio file
        const { uploadUrl, fileKey } = await fileUpload.generatePresignedUrl(userId, req.body.originalFilename)

        // Create a job record in DB with 'QUEUED' status and fileKey
        const job = await jobService.createJob(userId, fileKey, req.body.originalFilename)

        // Add the job to the BullMQ queue
        await jobService.addJobToQueue(job.id, fileKey)

        res.status(202).json({
            message: 'Audio upload initiated and job queued. Please upload file to the provided URL.',
            jobId: job.id,
            uploadUrl: uploadUrl,
            fileKey: fileKey
        })
    } catch (err) {
        next(err)
    }
}

export const getJobStatus = async (req, res, next) => {
    try {
        const userId = req.user.id
        const jobId = req.params.id // Job ID from URL Params?

        const job = await jobService.getJobById(jobId, userId)

        if (!job) {
            return res.status(404).json({
                message: 'Job not found!'
            })
        }

        res.status(200).json({
            jobId: job.id,
            status: job.status,
            transcript: job.transcript, // Deepl translated transcirpt
            summary: job.summary // Openai summary -- idk if its needed here
            // More if needed
        })
    } catch (err) {
        next(err)
    }
}


export const assAi = async (req, res, next) => {
    // Add a webhook handler for AssemblyAI 
    // This will be called by AssemblyAI, not directly be frontend at all
    // Will update the job status and trigger subsequent steps in the queue
    next()
}