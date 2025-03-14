CREATE TABLE IF NOT EXISTS users(
  id VARCHAR(32) NOT NULL,
  username VARCHAR(30) NOT NULL,
  password VARCHAR(256) NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS typingsessions(
  id VARCHAR(32) NOT NULL,
  userid VARCHAR(32) NOT NULL,
  wpm SMALLINT NOT NULL,
  accuracy SMALLINT NOT NULL,
  sessiontext TEXT NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS profiles(
  userid VARCHAR(32) NOT NULL,
  pfp VARCHAR(64) NOT NULL,

  FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (userid)
);