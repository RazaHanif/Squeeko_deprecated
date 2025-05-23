// Dedicated entry point for BullMQ workers

// Basic Imports
import { Queue, Worker } from 'bullmq'
import Redis from 'ioredis'

// Import config
import config from './config'