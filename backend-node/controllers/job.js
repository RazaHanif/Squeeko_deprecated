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
            message: 'Audio upload initiated and job queued. Please upload file to the provided URL.'
            
        })
    } catch (err) {
        next(err)
    }
}