const express = require("express")
const fs = require("fs").promises
const { randomUUID } = require("crypto")

const sql = require("./database")
const users = require("./userRoutes")

const DEFAULT_TEXT_PATH = "./notices/defaultText.txt"
const DEFAULT_TEXT_FRESH_TIME = 24 // in hours

class TextRouter {
  constructor() {
    this.m_defaultText = ""

    setInterval(
      () => {
        this.m_defaultText = ""
      },
      1000 * 3600 * DEFAULT_TEXT_FRESH_TIME
    )

    // define the routes
    this.router = express.Router()
    this.router.post("/generate", users.authUser, this.generateText.bind(this))
    this.router.post("/session", users.authUser, this.postSession.bind(this))
  }

  async generateText(req, res) {
    // load the text if they are not loaded in
    if (this.m_defaultText === "") {
      try {
        this.m_defaultText = await fs.readFile(DEFAULT_TEXT_PATH, "utf-8")
      } catch (err) {
        this.m_defaultText = ""
      }
    }

    // check if the notices are loaded in
    if (this.m_defaultText === "") {
      return res.status(500).json({
        error: "Internal server error!",
        text: ""
      })
    }

    res.status(200).json({
      error: null,
      text: this.m_defaultText
    })
  }

  async postSession(req, res) {
    const wpm = req.body.wpm
    const accuracy = req.body.accuracy
    const text = req.body.text

    // generate a new id for the session
    const id = randomUUID().replace(/-/g, "")
    try {
      await sql.dbExecute(
        `INSERT INTO typingsessions (id, userid, wpm, accuracy, sessiontext)
         VALUES (?, ?, ?, ?, ?)`,
         [id, req.auth.uid, wpm, accuracy, text]
      )

    } catch(err) {
      return res.status(500).json({
        error: "Internal server error!",
        session: undefined
      })
    }

    return res.status(201).json({
      error: null,
      session: {
        id: id,
        userid: req.auth.uid,
        wpm: wpm,
        accuracy: accuracy,
        text: text
      }
    })
  }
}

const text_router_handler = new TextRouter()

module.exports = text_router_handler.router