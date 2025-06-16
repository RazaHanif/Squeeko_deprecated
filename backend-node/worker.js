import { Queue, Worker } from 'bullmq'
import Redis from 'ioredis'
import config from './config'
import { processJob } from './workers/jobProcessor'

// Redis Connection
const connection = new Redis(config.redisUrl, {
    maxRetriesPerRequest: null,
    enableReadyCheck: false,
})

// Define Queue
// -- This should match queue name used in workers/queues.js
const transcriptionQueue = new Queue('transcriptionQueue', { connection })

// Worker setup
const worker = new Worker('transcriptionQueue', async (job) => {
    console.log(`Processing job ${job.id}: ${job.name}`)
    await processJob(job)
}, { connection, concurrency:
     config.workerConcurrency || 5
})

worker.on('completed', (job) => {
    console.log(`Job ${job.id} completed successfully`)
})

worker.on('failed', (job) => {
    // Should be proper error reporting here
    console.error(`Job ${job.id} failed`)
})

worker.on('error', (err) => {
    console.error('Worker error:', err)
})