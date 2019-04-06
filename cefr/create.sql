CREATE TABLE IF NOT EXISTS words_bymeaning (
 id integer PRIMARY KEY AUTOINCREMENT,
 frequency integer NOT NULL,
 level text NOT NULL,
 word text NOT NULL,
 pos text NOT NULL,
 meaning text NOT NULL,
 synopsis text,
 example1 text,
 example2 text
);

CREATE INDEX word_rank ON words_bymeaning (frequency);

CREATE TABLE IF NOT EXISTS us_bymeaning (
 id integer PRIMARY KEY AUTOINCREMENT,
 word_id integer NOT NULL,
 us_word text NOT NULL,
 FOREIGN KEY (word_id) REFERENCES words_bymeaning (id)
);

CREATE TABLE IF NOT EXISTS also_bymeaning (
 id integer PRIMARY KEY AUTOINCREMENT,
 word_id integer NOT NULL,
 also_words text NOT NULL,
 FOREIGN KEY (word_id) REFERENCES words_bymeaning (id)
);

CREATE TABLE IF NOT EXISTS family_words (
 id integer PRIMARY KEY AUTOINCREMENT,
 word text NOT NULL,
 family_words text NOT NULL
);

CREATE TABLE IF NOT EXISTS test_qnas (
 id integer PRIMARY KEY AUTOINCREMENT,
 user_id integer NOT NULL,
 seg integer NOT NULL,
 trial integer NOT NULL,
 time_text text NOT NULL,
 level integer NOT NULL,
 sub_level integer NOT NULL,
 word text NOT NULL,
 question text NOT NULL,
 answers text NOT NULL,
 result text NOT NULL
);
