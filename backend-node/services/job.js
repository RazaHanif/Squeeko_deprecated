// Main job logic

import prisma from '../db/prisma'
import { transcriptionQueue } from '../workers/queues'
import * as assemblyAI from './assemblyAi'
import * as deepL from './deepL'
import * as openAI from './openAi'
import * as alignment from '../utils/align'


export const createJobRecord = async (userId, fileKey, originalFilename) => {
    // TOOD: Check user's current usage quota before creating new job
    //       if quota exceeded throw error
    
    const job = await prisma.job.create({
        data: {
            userId,
            audioFileUrl: fileKey,
            originalFilename,
            status: 'QUEUED'
        }
    })
    return job
}

export const getJobById = async (jobId, userId) => {
    // Current user must be job user
    const job = await prisma.job.findUnique({
        where: {
            id: jobId,
            userId: userId 
        }
    })
    

    if(!job) {
        throw new Error('Job not found')
    }

    return job
}