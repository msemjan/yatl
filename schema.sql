DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (
  id              INTEGER     PRIMARY KEY AUTOINCREMENT,
  time            DATETIME    NOT NULL,
  title           TEXT        NOT NULL,
  description     TEXT        ,
  status          VARCHAR(50) NOT NULL,
  subtask_of_id   INTEGER     ,
  FOREIGN KEY     (subtask_of_id) REFERENCES tasks (id)
);

DROP TABLE IF EXISTS comments;
CREATE TABLE comments (
  id              INTEGER     PRIMARY KEY AUTOINCREMENT,
  time            DATETIME    NOT NULL,
  txt             TEXT        NOT NULL,
  task_id         INTEGER     NOT NULL,
  FOREIGN KEY     (task_id)   REFERENCES tasks (id)
);
