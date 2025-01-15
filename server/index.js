require("dotenv").config()
const express = require("express")
const path = require("path")
const bodyParser = require("body-parser")
const cors = require("cors")

const sql = require("./src/database")
const noticesRoutes = require("./src/retrieveInfoRoutes")
const userRoutes = require("./src/userRoutes")
const textRoutes = require("./src/textRoutes")
const generateText = require("./src/generateText")
const uploads = require("./src/uploads")

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

app.use("/api/users/upload/pfp", uploads.pfpUpload.single("pfp"))
app.use(uploads.errorHandling)

app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))

// ROUTES
app.use("/api/worker", generateText.router)
app.use("/api/notices", noticesRoutes)
app.use("/api/text", textRoutes)
app.use("/api/users", userRoutes.router)
app.use("/", express.static("pages"))
