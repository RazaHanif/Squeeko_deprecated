// Dedicated entry point for BullMQ workers

// Basic Imports
import { Queue, Worker } from 'bullmq'
import Redis from 'ioredis'

// Import config
import config from './config'

// Import job processor
import { processJob } from './workers/jobProcessor'

// Redis Connection
// -- Use a separate Redis instance for BullMQ
// -- Fly.io has a redis add on that can help with this
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

worker.on('completed', (job) => {
    console.log(`Job ${job.id} completed successfully`)
})

