// Auth Middleware

import jwt from 'jsonwebtoken'
import config from '../config'
// Import userService for user validation?

export const authenticateToken = (req, res, next) => {
    // TODO: Get token from Auth header (Bearer <TOKEN>)

    // TODO: Handle different JWT errors
    // TokenExpiredError, JsonWebTokenError...etc.
}

// TODO: Implement a middleware for checking specific roles/permissions
// export const authorizeRoles = (...roles) => { /* ... */ };