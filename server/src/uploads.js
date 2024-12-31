const express = require("express")
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

const pfpUpload = multer({ storage: pfpUploadStorage })

module.exports = {
  pfpUpload,
}
