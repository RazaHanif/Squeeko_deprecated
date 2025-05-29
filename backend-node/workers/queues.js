// BullMQ queues logic

import { Queue } from 'bullmq'
import Redis from 'ioredis'
import config from '../config'

const connection = new Redis(config.redisUrl, {
    maxRetriesPerRequest: null,
    enableReadyCheck: false,
})

// IDK if this is good or not?
export const transcriptionQueue = new Queue('transcriptionQueue', { connection })
export const translationQueue = new Queue('translationQueue', { connection })
export const summarizationQueue = new Queue('summarizationQueue', { connection })

// 