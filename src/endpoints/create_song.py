from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
create_song = Blueprint('song', __name__)

# logger
logger = logging.getLogger('api')

#! POST http://localhost:8080/dbproj/song
'''
  headers = {
    token: authentication token (artist)
  }
  payload = {
    'title': string,
    'release': 'YYYY-MM-DD',
    'duration': 'HH:MM:SS',
    'genre': 'genre',
    'label_id': 'label_id',
    'other_artists': ['artist_id1', 'artist_id2', ...] (optional)
  }
  return: {
    'status': status_code,
    'results': song_id if success,
    'error': error_message if any
  }
'''
@create_song.route('/', methods=['POST'])
def song():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  
  for field in ['title', 'release', 'duration', 'genre', 'label_id']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})

  #* Check if token is valid *#
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an artist *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM artist WHERE id = %s", (user_id, ))
    results = cur.fetchone()
    if results is None:
      logger.info(f'User {user_id} is not an artist')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an artist'})
    else:
      logger.debug(f'User {user_id} is an artist')

      # lock artist table (prevent same artist from being added twice)
      cur.execute("LOCK TABLE artist IN EXCLUSIVE MODE")

      #* Create song *#
      values = (payload['title'], payload['release'], payload['duration'], payload['genre'], payload['label_id'])
      cur.execute("INSERT INTO song (title, release, duration, genre, label_id) VALUES (%s, %s, %s, %s, %s) RETURNING ismn", values)
      song_id = cur.fetchone()[0]
      logger.info(f'Song {song_id} created')
      response = flask.jsonify({'status': StatusCodes['success'], 'results': song_id})

      #* Add artists *#
      # associate with artist from token
      cur.execute("INSERT INTO song_artist (song_ismn, artist_id) VALUES (%s, %s)", (song_id, user_id))
      logger.debug(f'Artist {user_id} added to song {song_id}')

      # associate with artists from payload
      if 'other_artists' in payload:
        for artist_id in payload['other_artists']:
          if artist_id == user_id: # skip if artist is the same as the one from token
            continue
          cur.execute("SELECT * FROM artist WHERE id = %s", (artist_id, ))
          if cur.fetchone() is None: # artist does not exist
            logger.info(f'Artist {artist_id} does not exist')
            continue

          cur.execute("INSERT INTO song_artist (song_ismn, artist_id) VALUES (%s, %s)", (song_id, artist_id))
          logger.debug(f'Artist {artist_id} added to song {song_id}')
      conn.commit()
      response = flask.jsonify({'status': StatusCodes['success'], 'results': song_id})
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response
