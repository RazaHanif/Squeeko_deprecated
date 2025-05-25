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

    // Error handling
    if(!job) {
        throw new Error('Job not found')
    }

    return job
}


export const addJobToQueue = async (jobId, fileKey) => {
    // Add to BullMQ queue for background processing
    // Job data should contain everyhing the workers need
    await transcriptionQueue.add(
        'processAudio',
        {
            jobId,
            fileKey
        } 
    )

    // Update job status to 'QUEUED' if not already set
}

export const handleAssAI = async (data) => {
    // TODO: Validate webhookData
    // Handle errors if validation fails

    const assAiJobId = data.id
    const status = data.status 
    const audioUrl = data.audio_url

    const job = await prisma.job.findUnique({
        where: {
            assAiJobId
        }
    })

    if (!job) {
        console.warn(`Webhook received for unkown job: ${assAiJobId}`)
        return new Error('Webook job id not found')
    }

    if (status === 'completed') {
        const originalTranscript = await assemblyAI.getTranscriptionResult(assAiJobId)
        await prisma.job.update({
            where: {
                id: job.id
            },
            data: {
                status: 'PROCESSING',
                assemblyOriginalTranscriptJson: originalTranscript,
                jobMinutesConsumed: data.audio_duraction / 60
            }
        })

        // Add new job to queue for translation
        await transcriptionQueue.add(
            'translateAndSummarize',
            { 
                jobId: job.id,
                originalTranscript
            }
        )
    } else if (status === 'error') {
        await prisma.job.update({
            where: {
                id: job.id
            },
            data: {
                status: 'FAILED',
                error: data.error
            }
        })
        // TODO: Notify user of error
    }
    // Handle other cases
}

// Func to be called by BullMQ workers
export default processTranslation = async (jobId, originalTranscript) => {
    
    // Translate the transcript with DeepL
    try {
        const translatedSegments = []
        let totalChar = 0
        for (const utterance of originalTranscript.utterances) {
            const translatedText = await deelL.translateText(utterance.text, 'en')
            translatedSegments.push({
                speaker: utterance.speaker,
                start: utterance.start,
                end: utterance.end,
                text: translatedText
            })
            totalChar += translatedText.length
        }

        await prisma.job.update({
            where: {
                id: jobId
            },
            data: {
                status: 'PROCESSING_SUMMARY',
                deepLTranslatedTranscriptJson: translatedSegments
            }
        })
    } catch (error) {
        console.error(`Error in translation for job: ${jobId}`, error)
        await prisma.job.update({
            where: {
                id: jobId
            },
            data: {
                status: 'FAILED',
                errorMessage: `Translation failed: ${error.message}`
            }
        })
    }
}

