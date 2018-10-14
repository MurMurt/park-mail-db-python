CREATE EXTENSION IF NOT EXISTS citext;


DROP TABLE IF EXISTS forum;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS vote;
DROP TABLE IF EXISTS thread;

-- USER --
CREATE TABLE IF NOT EXISTS users (
  fullname text,
  nickname  CITEXT NOT NULL,
  email CITEXT NOT NULL UNIQUE,
  about text,
  PRIMARY KEY (nickname)
);
--

-- FORUM  --
CREATE TABLE IF NOT EXISTS forum (
  slug CITEXT PRIMARY KEY,
  title TEXT NOT NULL,
  user_id INTEGER NOT NULL,
 );
--

-- THREAD --
CREATE TABLE IF NOT EXISTS thread (
  id SERIAL PRIMARY KEY,
  slug CITEXT UNIQUE ,
  forum_slug TEXT NOT NULL ,
  user_id INTEGER,
  title TEXT,
  message TEXT,
  created TIMESTAMP DEFAULT now(),

);
--

-- POST --
CREATE TABLE IF NOT EXISTS post (
  id SERIAL PRIMARY KEY ,
  parent INTEGER DEFAULT 0,
  author TEXT,
  message TEXT,
  isedited BOOLEAN,
  forum TEXT,
  created TIMESTAMP DEFAULT now(),
  thread INTEGER ,
  path INTEGER[]
);
--

-- VOTE --
CREATE TABLE IF NOT EXISTS vote (
  nickname TEXT,
  threadID INTEGER,
  voice int,
  forum CITEXT
);
