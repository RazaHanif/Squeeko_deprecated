const express = require('express')

const router = express.Router()
const {
  summarize
} = require('../controllers/summarize')

router.route('/').post(summarize)

module.exports = router
