const JWT_KEY_LEN = 64

function generateJWTKey() {
  const sequence = "1234567890abcdefghijklmnopqrstuvwxyz"
  let key = ""
  for (let i=0;i<JWT_KEY_LEN;++i) {
    const random_character = Math.floor(Math.random() * sequence.length)
    key += sequence[random_character]
  }

  return key
}

module.exports = {
  generateJWTKey
}