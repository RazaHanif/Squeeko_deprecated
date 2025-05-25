// Main auth logic

import bcrypt from 'bcrypt'
import jwt from 'jsonwebtoken'
import prisma from '../db/prisma'
import config from '../config'

const SALT_ROUNDS = 10 