CREATE TABLE IF NOT EXISTS users (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    name        TEXT        NOT NULL,
    email       TEXT        NOT NULL UNIQUE,
    password    TEXT        NOT NULL,
    created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friends (
    friend_1 INTEGER NOT NULL,
    friend_2 INTEGER NOT NULL,
    FOREIGN KEY (friend_1) REFERENCES users (id),
    FOREIGN KEY (friend_2) REFERENCES users (id),
    PRIMARY KEY (friend_1, friend_2)
);
