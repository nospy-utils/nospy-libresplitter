CREATE TABLE IF NOT EXISTS users (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    name        TEXT        NOT NULL,
    email       TEXT        NOT NULL UNIQUE,
    password    TEXT        NOT NULL,
    created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friends (
    friend_1    INTEGER NOT NULL,
    friend_2    INTEGER NOT NULL,
    FOREIGN KEY (friend_1) REFERENCES users (id),
    FOREIGN KEY (friend_2) REFERENCES users (id),
    PRIMARY KEY (friend_1, friend_2)
);

CREATE TABLE IF NOT EXISTS expenses (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_created    INTEGER     NOT NULL, --    user that created this expense
    currency        TEXT        NOT NULL, --    like: USD, BRL, NZD
    value           DOUBLE      NOT NULL,
    description     TEXT        NOT NULL,
    created_at      DATETIME    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_created)  REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS expense_user (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    expense_id      INTEGER NOT NULL,
    from_user_id    INTEGER NOT NULL,
    to_user_id      INTEGER NOT NULL,
    value           DOUBLE NOT NULL,
    FOREIGN KEY (expense_id)    REFERENCES expenses(id),
    FOREIGN KEY (from_user_id)  REFERENCES users(id),
    FOREIGN KEY (to_user_id)    REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS scheduled_expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_created INTEGER NOT NULL, --    user that created this expense
    currency     TEXT    NOT NULL, --    like: USD, BRL, NZD
    value        DOUBLE  NOT NULL,
    description  TEXT    NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    sched_day    INTEGER NOT NULL, --    to be filtered using strftime('%d', 'now')
    sched_end    DATE,             --    if null, it never ends
    FOREIGN KEY (user_created) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS scheduled_expense_user (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    sched_expense_id INTEGER NOT NULL,
    from_user_id     INTEGER NOT NULL,
    to_user_id       INTEGER NOT NULL,
    value            DOUBLE  NOT NULL,
    FOREIGN KEY (sched_expense_id) REFERENCES scheduled_expenses (id),
    FOREIGN KEY (from_user_id) REFERENCES users (id),
    FOREIGN KEY (to_user_id) REFERENCES users (id)
);
