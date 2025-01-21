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

class TextGenerator {
  constructor() {
    this.router = express.Router()

    this.workers = []

    // this.router.get("/generate", this.generateText.bind(this))
    this.router.post("/register", this.registerWorker.bind(this))
  }

  async generateText() {
    if (this.workers.length == 0) {
      throw Error("Text generation servers are unavailable!")
    }

    const selected_server = Math.floor(Math.random() * this.workers.length);
    const request_options = {
      hostname: this.workers[selected_server].host,
      port: this.workers[selected_server].port,
      path: "/generate",
      method: "POST",
    }

    const new_key = utils.generateJWTKey()
    const encrypted_key = crypto.publicEncrypt({
      key: this.workers[selected_server].public_key,
      padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
      oaepHash: "sha256"
    }, Buffer.from(new_key)).toString("base64")

    const token = {
      "token": jwt.sign(
        {key: encrypted_key},
        this.workers[selected_server].jwt_key
      )
    }
    this.workers[selected_server].jwt_key = new_key

    try {
      const result = await sendRequest(request_options, token)
      if (result.text == "") {
        throw Error("Internal server error!")
      }

      return result.text

    } catch(e) {
      console.log(e)
      throw Error("Internal server error!")
    }
  }

  registerWorker(req, res) {
    let data = req.body.payload
    jwt.verify(data, process.env.SHARED_SECRET, (err, decoded) => {
      if (err) {
        console.log("unable to verify")
        res.status(200).json({
          key: "",
          coworkers: []
        })
      } else {
        const new_key = utils.generateJWTKey()

        const encrypted_key = crypto.publicEncrypt({
          key: decoded.public_key,
          padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
          oaepHash: "sha256"
        }, Buffer.from(new_key)).toString("base64")

        const worker_server = {
          host: decoded.host,
          port: decoded.port,
        }

        // TODO: do binary search or something
        for (let i=0;i<this.workers.length;++i) {
          if ( this.workers[i].host == worker_server.host
            && this.workers[i].port == worker_server.port ) {
              this.workers.splice(i, 1)
              break;
            }
        }

        const coworkers_list = [ ...this.workers ]
        this.workers.push({
          host: decoded.host,
          port: decoded.port,
          partitions: decoded.partitions,
          public_key: decoded.public_key,
          jwt_key: new_key
        })
        console.log(this.workers)

        res.status(200).json({
          key: encrypted_key,
          coworkers: coworkers_list
        })
      }
    })
  }
}

const text_generator = new TextGenerator()

module.exports = {
  router: text_generator.router,
  generator: text_generator
}