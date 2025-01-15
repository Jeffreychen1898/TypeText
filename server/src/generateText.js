const http = require("http")
const express = require("express")
const jwt = require("jsonwebtoken")
const crypto = require("crypto")

const utils = require("./utils")

function sendRequest(options, message, jwtsecret) {
  //
}

// registeration:
//    host
//    port
//    public key

class TextGenerator {
  constructor() {
    this.router = express.Router()

    this.router.get("/generate", this.generateText.bind(this))
    this.router.post("/register", this.registerWorker.bind(this))
  }

  generateText(req, res) {
    const request_options = {
      hostname: "10.0.0.13",
      port: "8000",
      path: "/",
      method: "GET"
    }

    const request = http.request(request_options, (response) => {
      let data = ""

      response.on("data", (chunk) => {
        data += chunk
      })

      response.on("end", (chunk) => {
        console.log(data)
      })
    })

    request.on("error", (e) => {
      console.log(`[ERROR] ${e.message}`)
    })

    request.end()

    res.status(200).json({
      text: "Hello This is some text"
    })
  }

  registerWorker(req, res) {
    let data = req.body.payload
    jwt.verify(data, process.env.SHARED_SECRET, (err, decoded) => {
      if (err) {
        console.log("unable to verify")
        res.status(200).json({
          key: "",
          workers: []
        })
      } else {
        console.log(decoded)
        const new_key = utils.generateJWTKey()

        const encrypted_key = crypto.publicEncrypt({
          key: decoded.public_key,
          padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
          oaepHash: "sha256"
        }, Buffer.from(new_key)).toString("base64")
        console.log(new_key)
        res.status(200).json({
          key: encrypted_key,
          workers: []
        })
      }
      //res.send()
    })
  }
}

const text_generator = new TextGenerator()

module.exports = {
  router: text_generator.router
}