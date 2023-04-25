-- DROPING TABLES
DROP TABLE IF EXISTS song_playlist;
DROP TABLE IF EXISTS consumer_playlist;
DROP TABLE IF EXISTS song_artist;
DROP TABLE IF EXISTS album_artist;
DROP TABLE IF EXISTS prepaid_card_subscription;
DROP TABLE IF EXISTS album_song;
DROP TABLE IF EXISTS consumer_subscription;
DROP TABLE IF EXISTS consumer_song;
DROP TABLE IF EXISTS subscription;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS prepaid_card;
DROP TABLE IF EXISTS playlist;
DROP TABLE IF EXISTS album;
DROP TABLE IF EXISTS song;
DROP TABLE IF EXISTS consumer;
DROP TABLE IF EXISTS artist;
DROP TABLE IF EXISTS label;
DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS administrator;
DROP TABLE IF EXISTS credentials;

-- CREATING TABLES
CREATE TABLE credentials (
	id        BIGSERIAL NOT NULL,
	username  VARCHAR(32) NOT NULL,
	password  VARCHAR(128) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (username),
	CHECK (length(username) > 0),
	CHECK (length(password) > 0),
);

CREATE TABLE administrator (
	id BIGINT  NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (id) REFERENCES credentials(id)
);

CREATE TABLE person (
	id        BIGINT NOT NULL,
	name      VARCHAR(256) NOT NULL,
	address   VARCHAR(256) NOT NULL,
	email     VARCHAR(128) NOT NULL,
	birthdate DATE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (id) REFERENCES credentials(id),
	CHECK (length(name) > 0),
	CHECK (length(address) > 0),
	CHECK (length(email) > 0),
	UNIQUE (email)
);

CREATE TABLE label (
	id      BIGINT NOT NULL,
	name    VARCHAR(128) NOT NULL,
	contact VARCHAR(128) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name),
	CHECK (length(name) > 0),
	CHECK (length(contact) > 0)
);

CREATE TABLE artist (
	id            BIGINT NOT NULL,
	label_id      BIGINT NOT NULL,
	artistic_name VARCHAR(128) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (id) REFERENCES person(id),
	FOREIGN KEY (label_id) REFERENCES label(id),
	CHECK (length(artistic_name) > 0),
	UNIQUE (artistic_name) --! REVIEW
);

CREATE TABLE consumer (
	id BIGINT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (id) REFERENCES person(id)
);

CREATE TABLE song (
	ismn      BIGSERIAL NOT NULL,
	label_id  BIGINT NOT NULL,
	genre     VARCHAR(16) NOT NULL,
	title     VARCHAR(64) NOT NULL,
	release   DATE NOT NULL,
	duration  TIMESTAMP NOT NULL,
	PRIMARY KEY (ismn),
	FOREIGN KEY (label_id) REFERENCES label(id),
	CHECK (length(genre) > 0),
	CHECK (length(title) > 0)
);

CREATE TABLE album (
	id        BIGSERIAL,
	title     VARCHAR(64) NOT NULL,
	release   DATE NOT NULL,
	label_id  BIGINT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY (label_id) REFERENCES label(id),
	CHECK (length(title) > 0)
);

CREATE TABLE playlist (
	id      BIGSERIAL NOT NULL,
	name    VARCHAR(64) NOT NULL,
	private BOOL NOT NULL,
	PRIMARY KEY (id),
	CHECK (length(name) > 0)
);

CREATE TABLE prepaid_card ( --TODO
	id          VARCHAR(16) NOT NULL,
	consumer_id BIGINT NOT NULL,
	admin_id    BIGINT NOT NULL,
	amount      SMALLINT NOT NULL DEFAULT 0,
	limit_date  DATE NOT NULL,
	PRIMARY KEY (id, consumer_id),
	FOREIGN KEY (consumer_id) REFERENCES consumer(id),
	FOREIGN KEY (admin_id) REFERENCES administrator(id),
	CHECK (length(id) > 0)
);

CREATE TABLE comment (
	id            BIGSERIAL NOT NULL,
	content       TEXT NOT NULL,
	comment_date  DATE NOT NULL,
	song_ismn     BIGINT NOT NULL,
	consumer_id   BIGINT NOT NULL,
	parent_id     BIGINT,
	PRIMARY KEY (id),
	FOREIGN KEY (song_ismn) REFERENCES song(ismn),
	FOREIGN KEY (consumer_id) REFERENCES consumer(id),
	FOREIGN KEY (parent_id) REFERENCES comment(id),
	CHECK (length(content) > 0)
);

CREATE TABLE subscription ( --TODO
	id          BIGSERIAL NOT NULL,
	plan        VARCHAR(32) NOT NULL,
	start_date  DATE NOT NULL,
	end_date    DATE NOT NULL,
	PRIMARY KEY (id),
	CHECK (length(plan) > 0)
);

CREATE TABLE consumer_song (
	song_ismn   BIGINT NOT NULL,
	consumer_id BIGINT NOT NULL,
	listen_date DATE NOT NULL,
	views       SMALLINT NOT NULL DEFAULT 0,
	PRIMARY KEY (song_ismn, consumer_id),
	FOREIGN KEY (song_ismn) REFERENCES song(ismn),
	FOREIGN KEY (consumer_id) REFERENCES consumer(id)
); -- index on listen_date

CREATE TABLE consumer_subscription (
	consumer_id     BIGINT NOT NULL,
	subscription_id BIGINT NOT NULL,
	PRIMARY KEY (consumer_id, subscription_id),
	FOREIGN KEY (consumer_id) REFERENCES consumer(id),
	FOREIGN KEY (subscription_id) REFERENCES subscription(id)
);

CREATE TABLE album_song (
	album_id  BIGINT NOT NULL,
	song_ismn BIGINT NOT NULL,
	PRIMARY KEY (album_id, song_ismn),
	FOREIGN KEY (album_id) REFERENCES album(id),
	FOREIGN KEY (song_ismn) REFERENCES song(ismn)
);

CREATE TABLE prepaid_card_subscription (
	prepaid_card_id VARCHAR(16) NOT NULL,
	consumer_id     BIGINT NOT NULL,
	subscription_id BIGINT NOT NULL,
	PRIMARY KEY (prepaid_card_id, consumer_id, subscription_id),
	FOREIGN KEY (prepaid_card_id, consumer_id) REFERENCES prepaid_card(id, consumer_id),
	FOREIGN KEY (subscription_id) REFERENCES subscription(id)
);

CREATE TABLE album_artist (
	album_id  BIGINT,
	artist_id BIGINT,
	PRIMARY KEY (album_id, artist_id),
	FOREIGN KEY (album_id) REFERENCES album(id),
	FOREIGN KEY (artist_id) REFERENCES artist(id)
);

CREATE TABLE song_artist (
	song_ismn BIGINT,
	artist_id BIGINT,
	PRIMARY KEY (song_ismn, artist_id),
	FOREIGN KEY (song_ismn) REFERENCES song(ismn),
	FOREIGN KEY (artist_id) REFERENCES artist(id)
);

CREATE TABLE consumer_playlist (
	consumer_id BIGINT,
	playlist_id BIGINT,
	PRIMARY KEY (consumer_id, playlist_id),
	FOREIGN KEY (consumer_id) REFERENCES consumer(id),
	FOREIGN KEY (playlist_id) REFERENCES playlist(id)
);

CREATE TABLE song_playlist (
	song_ismn   BIGINT,
	playlist_id BIGINT,
	PRIMARY KEY (song_ismn, playlist_id),
	FOREIGN KEY (song_ismn) REFERENCES song(ismn),
	FOREIGN KEY (playlist_id) REFERENCES playlist(id)
);
