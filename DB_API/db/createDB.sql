CREATE EXTENSION IF NOT EXISTS citext;
-- --
set timezone = 'Europe/Moscow';
-- --
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS vote;
DROP TABLE IF EXISTS thread;
DROP TABLE IF EXISTS forum_user;
DROP TABLE IF EXISTS forum;
DROP TABLE IF EXISTS users;
-- --
-- USER --
CREATE TABLE IF NOT EXISTS users (
  fullname text,
  nickname CITEXT NOT NULL,
  email    CITEXT NOT NULL UNIQUE,
  about    text,
  id       SERIAL,
  PRIMARY KEY (nickname)
);
--
CREATE INDEX users_id_ind ON users(id);
-- --
-- FORUM  --
CREATE TABLE IF NOT EXISTS forum (
  slug      CITEXT PRIMARY KEY,
  title     TEXT   NOT NULL,
  user_nick CITEXT NOT NULL,
  threads INTEGER DEFAULT 0,
  posts INTEGER DEFAULT 0,
  FOREIGN KEY (user_nick) REFERENCES users (nickname)
);


--
-- FORUM_USER
CREATE TABLE  IF NOT EXISTS forum_user (
  forum CITEXT,
  user_id INTEGER,
  PRIMARY KEY (user_id, forum)
);


-- THREAD --
CREATE TABLE IF NOT EXISTS thread (
  id      SERIAL PRIMARY KEY,
  slug    CITEXT UNIQUE,
  forum   CITEXT                   NOT NULL,
  author  CITEXT,
  title   TEXT                     NOT NULL,
  message TEXT,
  votes   INTEGER                           DEFAULT 0,
--   posts   INTEGER                           DEFAULT 0,
  created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (author) REFERENCES users (nickname),
  FOREIGN KEY (forum) REFERENCES forum (slug)
);

-- --

CREATE OR REPLACE FUNCTION threadInc()
  RETURNS TRIGGER AS
$BODY$
BEGIN
  INSERT INTO forum_user (forum, user_id)
  VALUES (new.forum, (SELECT id FROM users WHERE nickname = new.author))
  ON CONFLICT DO NOTHING;
  UPDATE forum SET threads = threads + 1 WHERE slug = new.forum;
  RETURN new;
END;
$BODY$
LANGUAGE plpgsql;

CREATE TRIGGER threadInс
  AFTER INSERT
  ON thread
  FOR EACH ROW EXECUTE PROCEDURE threadInc();
-- --
-- POST --
CREATE TABLE IF NOT EXISTS post (
  id        SERIAL PRIMARY KEY,
  author    CITEXT                   NOT NULL,
  message   TEXT                     NOT NULL,
  thread_id INTEGER                  NOT NULL,
  FOREIGN KEY (parent_id) REFERENCES post (id),
  FOREIGN KEY (author) REFERENCES users (nickname),
  FOREIGN KEY (thread_id) REFERENCES thread (id),
  parent_id INTEGER,
  path      INTEGER [],
  created   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  is_edited BOOLEAN                           DEFAULT FALSE
);

CREATE INDEX posts__thread_id_created_ind
  ON post (thread_id, id, created);
--
-- --
-- VOTE --
CREATE TABLE IF NOT EXISTS vote (
  nickname  CITEXT  NOT NULL,
  thread_id INTEGER NOT NULL,
  voice     INTEGER NOT NULL,
  FOREIGN KEY (nickname) REFERENCES users (nickname),
  FOREIGN KEY (thread_id) REFERENCES thread (id),
  CONSTRAINT unique_votes UNIQUE (nickname, thread_id)
);
-- --
CREATE OR REPLACE FUNCTION vote_update()
  RETURNS TRIGGER AS
$BODY$
BEGIN
  IF old.voice = -1 AND new.voice = 1
  THEN
    UPDATE thread SET votes = votes + 2 WHERE id = new.thread_id;
  END IF;
  IF old.voice = 1 AND new.voice = -1
  THEN
    UPDATE thread SET votes = votes - 2 WHERE id = new.thread_id;
  END IF;
  RETURN new;
END;
$BODY$
LANGUAGE plpgsql;
-- --
CREATE TRIGGER voteUpdate
  BEFORE UPDATE
  ON vote
  FOR EACH ROW EXECUTE PROCEDURE vote_update();
-- --
-- --
CREATE OR REPLACE FUNCTION vote_insert()
  RETURNS TRIGGER AS
$BODY$
BEGIN
  UPDATE thread SET votes = votes + new.voice WHERE id = new.thread_id;
  RETURN new;
END;
$BODY$
LANGUAGE plpgsql;
-- --
CREATE TRIGGER voteInsert
  AFTER INSERT
  ON vote
  FOR EACH ROW EXECUTE PROCEDURE vote_insert();