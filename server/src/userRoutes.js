const express = require("express")
const { randomUUID } = require("crypto")
const bcrypt = require("bcrypt")
const jwt = require("jsonwebtoken")

const sql = require("./database")

const router = express.Router()

const BCRYPT_SALT_ROUNDS = parseInt(process.env.BCRYPT_SALT_ROUNDS)
const JWT_KEY = process.env.JWT_SECRET_KEY
const WPM_AVERAGE_COUNT = 100

const authUser = (req, res, next) => {
  const uid = req.body.authtoken // validate token
  req.auth = {
    uid: uid,
  }
  // if unauthenticated, call res.status(403).json({error: "Invalid token!"})
  next()
}

// todo: optimize this route a bit more
router.post("/profile", authUser, async (req, res) => {
  let profile_info = {}

  try {
    // retrieve the data
    const user = await sql.dbFetchOne(
      `SELECT id, created FROM users WHERE id = ?`,
      [req.auth.uid]
    )
    if (!user) {
      return res.status(403).json({
        error: "Invalid username!",
        target: "/profile",
        user: undefined,
      })
    }

    const pfp = await sql.dbFetchOne(
      `SELECT pfp FROM profiles WHERE userid = ?`,
      [req.auth.uid]
    )

    const typing_speeds = await sql.dbFetchAll(
      `SELECT wpm FROM typingsessions WHERE userid = ? ORDER BY created DESC LIMIT ?`,
      [req.auth.uid, WPM_AVERAGE_COUNT]
    )

    // calculate average typing speed
    let typing_average = 0;
    let num_datapoints = 0;
    for (const speed of typing_speeds) {
      typing_average += speed.wpm
      num_datapoints ++
    }
    if (num_datapoints > 0)
      typing_average /= num_datapoints
    else
      typing_average = 0

    const session_count = await sql.dbFetchOne(
      `SELECT COUNT(*) AS count FROM typingsessions WHERE userid = ?`,
      [req.auth.uid]
    )

    profile_info = {
      userid: user.id,
      username: user.username,
      created: user.created,
      pfp: pfp.pfp,
      wpm: typing_average,
      sessions: session_count.count,
    }
  } catch (err) {
    console.log(err)
    return res.status(500).json({
      error: "Internal server error!",
      target: "/profile",
      user: undefined,
    })
  }

  // return the data
  return res.status(200).json({
    error: null,
    target: "/profile",
    user: profile_info,
  })
})

router.post("/changepassword", authUser, async (req, res) => {
  const old_password = req.body.oldpassword
  const new_password1 = req.body.password1
  const new_password2 = req.body.password2

  // ensure the password is typed correctly
  if (new_password1 !== new_password2) {
    return res.status(403).json({
      error: "The two passwords provided are not the same!",
      target: "/profile",
      user: undefined,
    })
  }

  let user = undefined
  try {
    // validate the old password
    user = await sql.dbFetchOne(
      `SELECT username, password, created FROM users WHERE id = ?`,
      [req.auth.uid]
    )

    const entered_old_pass = user ? old_password : ""
    const password_match = await bcrypt.compare(entered_old_pass, user.password)
    if (!password_match) {
      return res.status(401).json({
        error: "Invalid password!",
        target: "/profile",
        user: undefined,
      })
    }

    // update the password
    const hashed_password = await bcrypt.hash(new_password1, BCRYPT_SALT_ROUNDS)
    await sql.dbExecute(`UPDATE users SET password = ? WHERE id = ?`, [
      hashed_password,
      req.auth.uid,
    ])
  } catch (err) {
    return res.status(500).json({
      error: "Internal server error!",
      target: "/profile",
      user: undefined,
    })
  }

  return res.status(201).json({
    error: null,
    target: "/profile",
    user: {
      id: req.auth.uid,
      username: user.username,
      created: user.created,
    },
  })
})

router.post("/upload/pfp", authUser, async (req, res) => {
  try {
    // retrieve the user profile
    const profile = await sql.dbFetchOne(
      `SELECT pfp, wpm, numsessions FROM profiles WHERE userid = ?`,
      [req.auth.uid]
    )

    if (!profile) {
      return res.status(200).json({
        error: null,
        target: "/profile",
        user: undefined,
      })
    }

    // set the profile picture
    await sql.dbExecute(`UPDATE profiles SET pfp = ? WHERE userid = ?`, [
      req.file.filename,
      req.auth.uid,
    ])
  } catch (err) {
    return res.status(500).json({
      error: "Internal server error!",
      target: "/profile",
      user: undefined,
    })
  }

  return res.status(200).json({
    error: null,
    target: "/profile",
    user: {
      userid: profile.userid,
      pfp: req.file.filename,
      wpm: profile.wpm,
      numsessions: profile.numsessions,
    },
  })
})

router.post("/login", async (req, res) => {
  const username = req.body.username
  const password = req.body.password

  if (username == "" || password == "") {
    return res.status(401).json({
      error: "Invalid username or password",
      target: "/login",
      user: undefined,
    })
  }

  let user = undefined

  try {
    // retrieve the user
    user = await sql.dbFetchOne(`SELECT * FROM users WHERE username = ?`, [
      username,
    ])

    if (!user) {
      return res.status(401).json({
        error: "Invalid username or password",
        target: "/login",
        user: undefined,
      })
    }

    // check password to authenticate user
    const password_match = await bcrypt.compare(password, user.password)
    if (!password_match) {
      return res.status(401).json({
        error: "Invalid username or password",
        target: "/login",
        user: undefined,
      })
    }
  } catch (err) {
    return res.status(500).json({
      error: "Internal server error!",
      target: "/login",
      user: undefined,
    })
  }

  // return the result
  const token = jwt.sign({ uid: user.id }, JWT_KEY)

  return res.status(200).json({
    error: null,
    target: "/",
    user: {
      id: user.id,
      username: username,
      created: user.created,
      loginToken: token,
    },
  })
})

router.post("/register", async (req, res) => {
  const username = req.body.username
  const password1 = req.body.password1
  const password2 = req.body.password2

  if (username == "" || password1 == "") {
    return res.status(400).json({
      error: "The username or password field is empty!",
      target: "/login",
      user: undefined,
    })
  }

  // assert passwords are the same
  if (password1 !== password2) {
    return res.status(400).json({
      error: "The two passwords provided are not the same!",
      target: "/login",
      user: undefined,
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
        user: undefined,
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
      `INSERT INTO profiles (userid, pfp)
       VALUES (?, ?)`,
      [userid, ""]
    )
  } catch (err) {
    console.log(err)
    // internal server error
    return res.status(500).json({
      error: "Internal server error!",
      target: "/login",
      user: undefined,
    })
  }

  // successfully registered
  res.status(201).json({
    error: null,
    target: "/login",
    user: {
      id: userid,
      username: username,
      profile: "",
    },
  })
})

module.exports = {
  router,
  authUser,
}
