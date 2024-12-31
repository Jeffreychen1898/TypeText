const express = require("express")
const { randomUUID } = require("crypto")
const bcrypt = require("bcrypt")
const jwt = require("jsonwebtoken")

const sql = require("./database")

const router = express.Router()

const BCRYPT_SALT_ROUNDS = process.env.BCRYPT_SALT_ROUNDS
const JWT_KEY = process.env.JWT_SECRET_KEY

router.post("/login", async (req, res) => {
  const username = req.body.username
  const password = req.body.password

  let user = undefined

  try {
    // retrieve the user
    user = await sql.dbFetchOne(
      `SELECT * FROM users WHERE username = ?`,
      [username]
    )

    if (!user) {
      return res.status(401).json({
        error: "Invalid username or password",
        target: "/login",
        user: undefined
      })
    }

    // check password to authenticate user
    const password_match = await bcrypt.compare(password, user.password)
    if (!password_match) {
      return res.status(401).json({
        error: "Invalid username or password",
        target: "/login",
        user: undefined
      })
    }
  } catch (err) {
    return res.status(500).json({
      error: "Internal server error!",
      target: "/login",
      user: undefined
    })
  }

  // return the result
  const token = jwt.sign({ uname: user.username }, JWT_KEY)

  return res.status(200).json({
    error: null,
    target: "/",
    user: {
      id: user.id,
      username: username,
      created: user.created,
      loginToken: token
    }
  })
})

router.post("/register", async (req, res) => {
  const username = req.body.username
  const password1 = req.body.password1
  const password2 = req.body.password2

  // assert passwords are the same
  if (password1 !== password2) {
    return res.status(400).json({
      error: "The two passwords provided are not  the same!",
      target: "/login",
      user: undefined
    })
  }

  const userid = randomUUID().replace(/-/g, "")

  try {
    // assert the username is not taken
    const result = await sql.dbFetchOne(
      `SELECT * FROM users WHERE username = ?`,
      [username]
    )

    if (result) {
      return res.status(409).json({
        error: "The username has already been used!",
        target: "/login",
        user: undefined
      })
    }

    // hash the password
    const hashed_password = await bcrypt.hash(password1, BCRYPT_SALT_ROUNDS)

    //create the user
    const user_parameters = [userid, username, hashed_password]
    await sql.dbExecute(
      `INSERT INTO users (id, username, password)
       VALUES (?, ?, ?)`,
       user_parameters
    )
    await sql.dbExecute(
      `INSERT INTO profiles (userid, pfp, wpm, numsessions)
       VALUES (?, ?, ?, ?)`,
       [userid, "", 0, 0]
    )

  } catch(err) {
    console.log(err)
    // internal server error
    return res.status(500).json({
      error: "Internal server error!",
      target: "/login",
      user: undefined
    })
  }

  // successfully registered
  res.status(201).json({
    error: null,
    target: "/login",
    user: {
      id: userid,
      username: username,
      profile: ""
    }
  })
})

module.exports = router