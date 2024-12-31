const multer = require("multer")
const path = require("path")
const { randomUUID } = require("crypto")

const pfpUploadStorage = multer.diskStorage({
  destination: (req, file, callback) => {
    callback(null, "uploads/pfp/")
  },
  filename: (req, file, callback) => {
    const fileid = randomUUID().replace(/-/g, "")
    const filename = fileid + path.extname(file.originalname)
    callback(null, filename)
  },
})

const pfpUploadRestrictions = (req, file, callback) => {
  const allowedTypes = ["image/jpeg", "image/png"]

  if (!allowedTypes.includes(file.mimetype)) {
    return callback(new Error("Invalid file type!"), false)
  }

  callback(null, true)
}

const pfpUpload = multer({
  storage: pfpUploadStorage,
  fileFilter: pfpUploadRestrictions,
  limits: {
    fileSize: 5 * 1024 * 1024,
  },
})

const errorHandling = (err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    return res.status(500).json({
      error: "Internal server error!",
    })
  }

  if (err) {
    return res.status(403).json({
      error: err.message,
    })
  }

  next()
}

module.exports = {
  pfpUpload,
  errorHandling,
}
