const express = require("express")
const fs = require("fs").promises

const NOTICES_FILEPATH = "./notices/notice.txt"
const NOTICES_REFRESH_TIME = 24 // in hours

class InfoRouter {
  constructor() {
    this.m_notices = ""

    // reset the notices every few hours
    // 1000 millisec / sec * 3600 sec / hr * num hours
    setInterval(
      () => {
        this.m_notices = ""
      },
      1000 * 3600 * NOTICES_REFRESH_TIME
    )

    // define the routes
    this.router = express.Router()
    this.router.get("/retrieve", this.getNotices.bind(this))
  }

  async getNotices(req, res) {
    // load the notices if they are not loaded in
    if (this.m_notices === "") {
      try {
        this.m_notices = await fs.readFile(NOTICES_FILEPATH, "utf-8")
      } catch (err) {
        this.m_notices = ""
      }
    }

    // check if the notices are properly loaded in
    if (this.m_notices !== "") {
      res.status(200).send({
        valid: true,
        notices: this.m_notices,
      })
    } else {
      res.status(404).send({
        valid: false,
        notices: "",
      })
    }
  }
}

const info_router_handler = new InfoRouter()

module.exports = info_router_handler.router
