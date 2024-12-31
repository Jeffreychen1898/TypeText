const sqlite3 = require("sqlite3").verbose()

let db = undefined

function dbConnect(path, callback) {
  db = new sqlite3.Database(path, callback)
}

function dbFetchOne(query, parameters) {
  return new Promise((resolve, reject) => {
    if (!db) return reject("[ERROR] Database is not connected!")

    db.get(query, parameters, (err, row) => {
      if (err) return reject(err)

      return resolve(row)
    })
  })
}

function dbFetchAll(query, parameters) {
  return new Promise((resolve, reject) => {
    if (!db) return reject("[ERROR] Database is not connected!")

    db.all(query, parameters, (err, rows) => {
      if (err) return reject(err)

      return resolve(rows)
    })
  })
}

function dbExecute(query, parameters) {
  return new Promise((resolve, reject) => {
    if (!db) return reject("[ERROR] Database is not connected!")

    db.run(query, parameters, (err) => {
      if (err) reject(err)

      return resolve({})
    })
  })
}

module.exports = {
  dbConnect,
  dbFetchOne,
  dbFetchAll,
  dbExecute,
}
