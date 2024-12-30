const express = require("express")

const app = express()

const PORT = 8000

function serverOnLoad() {
  console.log(`Server started on port: ${PORT}`)
}

app.listen(PORT, serverOnLoad)

app.get("/", (req, res) => {
	res.send("Hello World!")
})
