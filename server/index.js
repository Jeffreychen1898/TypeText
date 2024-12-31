require("dotenv").config()
const express = require("express")
const path = require("path")
const bodyParser = require("body-parser")
const cors = require("cors")

const sql = require("./src/database")
const noticesRoutes = require("./src/retrieveInfoRoutes")
const userRouters = require("./src/userRoutes")

const app = express()

const PORT = process.env.PORT || 8000

function serverOnLoad() {
  console.log(`Server started on port: ${PORT}`)
}

function databaseOnConnect(err) {
  if (err) {
    console.error("[ERROR] opening database file: ", err.message)
  } else {
    // start the server
    console.log("Connected to Sqlite database")
    app.listen(PORT, serverOnLoad)
  }
}

sql.dbConnect(path.join(__dirname, "sqlite", "database.db"), databaseOnConnect)

// middlewares
app.use(cors())
//app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))

// ROUTES
app.use("/api/notices", noticesRoutes)
app.use("/api/users", userRouters)
app.use("/", express.static("pages"))
