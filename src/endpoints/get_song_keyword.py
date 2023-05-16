from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
get_song_keyword = Blueprint('searchSong', __name__)

# logger
logger = logging.getLogger('api')

#! GET http://localhost:8080/dbproj/song/{keyword}
'''
  header: {
    token: auth token (consumer)
  }
  return: {
    'status': status_code,
    'results': [
      {'title': title, 'label_id': label_id, 'artists': [artist_id, ...], 'albums': [album_id, ...]},
      ...
    ]
    'error': error message
  }
'''
@get_song_keyword.route('/<keyword>', methods=['GET'])
def searchSong(keyword):
  token = flask.request.headers.get('token')
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})

  #* Check if token is valid *#
  jwt_decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an Consumer *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM consumer WHERE id = %s", (user_id, ))
    if cur.fetchone() is None:
      logger.info(f'User {user_id} is not a consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not a consumer'})
    else:
      logger.debug(f'User {user_id} is a consumer')
      #* Get songs *#
      value = '%' + keyword + '%'
      # check title, genre, artist_name, album_name
      query = '''
        SELECT song.ismn, song.title as title, song.label_id as label,
          array_agg(artist.artistic_name) as artists,
          array_agg(album.id) FILTER (WHERE album.id IS NOT NULL) as albums
        FROM song
        LEFT JOIN song_artist ON song.ismn = song_artist.song_ismn
        LEFT JOIN artist      ON song_artist.artist_id = artist.id
        LEFT JOIN album_song  ON song.ismn = album_song.song_ismn
        LEFT JOIN album       ON album_song.album_id = album.id
        WHERE song.title LIKE %s
        GROUP BY song.ismn, song.title, song.label_id
      '''
      cur.execute(query, ('%' + value + '%', ))
      results = cur.fetchall()
      output = []
      for result in results:
        output.append({
          'title': result[1],
          'label_id': result[2],
          'artists': result[3],
          'albums': result[4]
        })
      response = flask.jsonify({'status': StatusCodes['success'], 'results': output})
  except (Exception, psycopg2.DatabaseError) as error:
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response
