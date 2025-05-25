// Main auth logic

import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'
import prisma from '../db/prisma'
import config from '../config'

const SALT_ROUNDS = 10 

export const registerUser = async (email, password, firstName, lastName) => {
    // Check if user with email already exists
    // if (user) { error }

    const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS)

    const user = await prisma.user.create({
        data: {
            email,
            passwordHash: hashedPassword,
            firstName,
            lastName
        }
    })
    // Remove hashed password from user object
    // user.data.passwordHash = '***' ??
    return user
}

export const loginUser = async (email, password) => {
    
}