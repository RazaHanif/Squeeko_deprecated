// Centralized config file

// Load env variables from .env
import dotenv from 'dotenv'

dotenv.config()

const config = {
    port: process.env.PORT || 3000,
    nodeEnv: process.env.NODE_ENV || 'development',
    databaseUrl: process.env.DATABASE_URL,
    redisUrl: process.env.REDIS_URL,

    // API Keys
    assemblyAI: {
        apiKey: process.env.ASSEMBLYAI_API_KEY,
        webhookSecret: process.env.ASSEMBLYAI_WEBHOOK_SECRET
    },
    deepl: {
        apiKey: process.env.DEEPL_API_KEY,
    },
    openai: {
        apiKey: process.env.OPENAI_API_KEY,
    },
    stripe: {
        apiKey: process.env.STRIPE_API_KEY,
        webhookSecret: process.env.STRIPE_WEBHOOK_SECRET
    },

    // Cloud Storage (AWS S3)
    cloudStorage: {
        bucketName: process.env.CLOUD_STORAGE_BUCKET_NAME,
        region: process.env.CLOUD_STORAGE_REGION,
        accessKeyId: process.env.CLOUD_STORAGE_ACCESS_KEY_ID,
        secretAccessKey: process.env.CLOUD_STORAGE_SECRET_ACCESS_KEY,
        endpoint: process.env.CLOUD_STORAGE_ENDPOINT,
    },

    jwtSecret: process.env.JWT_SECRET,
    workerConcurrency: parseInt(process.env.WORKER_CONCURRENCY || '5', 10),
    freeTierUsage: process.env.FREE_TIER_USAGE,
    paidTierUsage: process.env.PAID_TIER_USAGE,

}

// Basic validation
// TODO: Add more checks for critical env vars
if (!config.databaseUrl) {
    console.error('FATAL ERROR: DATABASE_URL is not defined!')
    process.exit(1)
}

export default config