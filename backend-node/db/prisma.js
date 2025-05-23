// Basic Prisma file

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient({
    log: [
        'query', 
        'info',
        'warn',
        'error'
    ]
})

// TODO: Add connection tests here

export default prisma