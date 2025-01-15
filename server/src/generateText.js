const http = require("http")
const express = require("express")
const jwt = require("jsonwebtoken")
const crypto = require("crypto")

const utils = require("./utils")

/* options {hostname, port, path, method} */
function sendRequest(options, message) {
  const request_options = {
    hostname: options.hostname,
    port: options.port,
    path: options.path,
    method: options.method,
    headers: {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(JSON.stringify(message))
    },
    timer: 5000
  }

  return new Promise((resolve, reject) => {
    // send the request
    const request = http.request(request_options, (response) => {
      let data = ""

      response.on("data", (chunk) => {
        data += chunk
      })

      response.on("end", (_) => {
        return resolve(JSON.parse(data))
      })
    })

    request.write(JSON.stringify(message))

    // errors
    request.on("error", (e) => {
      return reject(e)
    })
    request.on("timeout", () => {
      return reject("[ERROR] request timeout!")
    })

    request.end()
  })
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

  async generateText(req, res) {
    const request_options = {
      hostname: "127.0.0.1",
      port: "8000",
      path: "/generate",
      method: "POST",
    }

    const token = {
      "token": jwt.sign({key: "nokey"}, "nokey")
    }

    try {
      const result = await sendRequest(request_options, token)
      res.status(200).json({
        error: null,
        text: result.text
      })

    } catch(e) {
      console.log(e)
      return res.status(500).json({
        error: "[ERROR] Internal server error!",
        text: "[ERROR] Internal server error!"
      })
    }
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