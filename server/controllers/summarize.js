import OpenAI from 'openai'
const openai = new OpenAI({
    apiKey: process.env.TEST_API_KEY
})

const model = 'gpt-4o-mini'

const completiopn = openai.chat.completions.create({
    model: model,
    store
})

const getJob = async (req, res) => {
  const {
    user: { userId },
    params: { id: jobId },
  } = req

  const job = await Job.findOne({
    _id: jobId,
    createdBy: userId,
  })
  if (!job) {
    throw new NotFoundError(`No job with id ${jobId}`)
  }
  res.status(StatusCodes.OK).json({ job })
}

module.exports = {
  getJob,
}
