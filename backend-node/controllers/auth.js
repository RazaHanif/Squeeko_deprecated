// Request handler for Auth routes
import * as authService from '../services/auth'

export const register = async (req, res, next) => {
    try {
        // TODO: Validate req.body (email, password, etc) using Joi/Zod
        const { email, password, firstName, lastName } = req.body
        const user = await authService.registerUser(
            email, 
            password, 
            firstName, 
            lastName 
        )
        // TOOD: Generate JWT for new user
        res.status(201).json({ 
            message: "User registered sucessfully", 
            user: { id: user.id, email: user.email}
            /*token*/ 
        })
    } catch (err) {
        next(err)
    }
}

export const login = async (req, res, next) => {
    try {
        // TODO: Validate req.body (email, password)
        const { email, password } = req.body
        const { user, token } = await authService.loginUser(
            email,
            password
        )
        res.status(200).json({ 
            message: 'Logged in successfully',
            user: { id: user.id, email: user.email },
            /*token*/
        })
    } catch (err) {
        next(err)
    }
}