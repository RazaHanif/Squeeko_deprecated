// Auth Middleware

// Basic Imports
import jwt from 'jsonwebtoken'
import config from '../config'
// Import userService for user validation?

export const authenticateToken = (req, res, next) => {
    // TODO: Get token from Auth header (Bearer <TOKEN>)
    const authHeader = req.headers['authorization']
    const token = authHeader && authHeader.split(' ')[1]

    if (!token) {
        return res.status(401).json({ message: 'Authentication token is missing'})
    }

    jwt.verify(token, config.jwtSecret, (err, user) => {
        if (err) {
            // TODO: Handle different JWT errors
            // TokenExpiredError, JsonWebTokenError...etc.
            return res.status(403).json({ message: "Invalid or expired token." })
        }
        req.user = user
        next()
    })
}

// TODO: Implement a middleware for checking specific roles/permissions
// export const authorizeRoles = (...roles) => { /* ... */ };