import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'
import prisma from '../db/prisma'
import config from '../config'

const SALT_ROUNDS = 10 

export const registerUser = async (email, password, firstName, lastName) => {
    // Check if user with email already exists
    const userExists = await prisma.user.findUnique({
        where: { email }
    })

    if (userExists) {
        throw new Error('User already exists')
    }

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
    const user = await prisma.user.findUnique({
        where: { email }
    })
    if (!user) {
        throw new Error('Invalid credentials') // Wanna keep it lowkey vauge
    }

    const isPasswordValid = await bcrypt.compare(password, user.passwordHash)
    if (!isPasswordValid) {
        throw new Error('Invalid credentials')
    }

    // TODO: Generate JWT token
    const token = jwt.sign(
        {
            id: user.id,
            email: user.email,
        },
        config.jwtSecret,
        {
            expiresIn: '1h' // Adjust later
        }
    )

    // TODO: Update last_login_at in db

    return { user, token }
}

// findUserById
// updateUser