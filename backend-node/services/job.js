// Main job logic

import prisma from '../db/prisma'
import { transcriptionQueue } from '../workers/queues'
import * as assemblyAI from './assemblyAi'
import * as deepL from './deepL'
import * as openAI from './openAi'
