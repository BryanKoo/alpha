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
