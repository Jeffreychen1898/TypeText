const express = require("express")

const noticesRoutes = require("./src/retrieveInfoRoutes")

const app = express()

const PORT = 8000

function serverOnLoad() {
  console.log(`Server started on port: ${PORT}`)
}

app.listen(PORT, serverOnLoad)

// ROUTES
app.use("/api", noticesRoutes)
app.use("/", express.static("pages"))
