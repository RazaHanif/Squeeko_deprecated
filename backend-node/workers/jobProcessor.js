// Func to process jobs from queue will go here

import * as jobService from '../services/job'
import * as assemblyaiService from '../services/assemblyAi'
import * as deeplService from '../services/deepL'
import * as openaiService from '../services/openAi'
import * as alignment from '../utils/align'
import prisma from '../db/prisma' 

export const processJob = async (job) => {
    const { jobId, fileKey } = job.data

    try {
        // Step 1
        await prisma.job.update({
            where: { id: jobId },
            data: { status: 'PROCESSING_STT' }
        })
        const webhookUrl = `${config.appBaseUrl}/api/webhooks/assemblyai`
        const assemblyaiResponse = await assemblyaiService.startTranscription(fileKey, webhookUrl)
        
        await prisma.job.update({
            where: { id: jobId },
            data: {
                assemblyaiJobId: assemblyaiResponse.id,
            }
        })

        // TODO: The rest of the pipeline (DeepL, OpenAI) will be triggered by AssemblyAI Webhook
        // Which wll then add *new* job to the queue (translate&summarize)


    } catch (err) {
        console.error(`Failed to process job ${jobId} at STT initiation step:`, err)
        await prisma.job.update({
            where: { id: jobId },
            data: {
                status: 'FAILED',
                errorMessage: `STT initiation failed: ${err.message}`
            }
        })
        throw err
    }
}

// HINT: You'll likely have another job type for the translation/summarization step,
//       triggered by the AssemblyAI webhook.
//       Example:
// export const processTranslateAndSummarizeJob = async (job) => {
//     const { jobId, originalTranscript } = job.data;
//     await jobService.processTranslationAndSummarization(jobId, originalTranscript);
// };

// HINT: Your worker.js will listen for different job names and call the appropriate processor functions.
// 