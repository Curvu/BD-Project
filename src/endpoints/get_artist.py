from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
get_artist = Blueprint('artist', __name__)

# logger
logger = logging.getLogger('api')

#! GET http://localhost:8080/dbproj/artist_info/{artist_id}
'''
  header: {
    token: auth token (consumer)
  }
  return: {
    'status': status_code,
    'results': {
      'name': artist_name,
      'songs': [song_id, ...],
      'albums': [album_id, ...],
      'playlists': [playlist_id, ...]
    },
    'error': error message
'''
@get_artist.route('/<artist_id>', methods=['GET'])
def artist(artist_id):
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
      #* Get artist info *#
      query = '''
        SELECT DISTINCT artist.artistic_name as artist,
          array_agg(song.ismn) FILTER (WHERE song.ismn IS NOT NULL) as songs,
          array_agg(DISTINCT album.id) FILTER (WHERE album.id IS NOT NULL) as albums,
          array_agg(DISTINCT song_playlist.playlist_id) FILTER (WHERE song_playlist.playlist_id IS NOT NULL) as playlists
        FROM artist
        LEFT JOIN song_artist   ON artist.id = song_artist.artist_id
        LEFT JOIN song          ON song_artist.song_ismn = song.ismn
        LEFT JOIN album_song    ON song.ismn = album_song.song_ismn
        LEFT JOIN album         ON album_song.album_id = album.id
        LEFT JOIN song_playlist ON song.ismn = song_playlist.song_ismn
        WHERE artist.id = %s
        GROUP BY artist
      '''
      cur.execute(query, (artist_id, ))
      results = cur.fetchone()
      response = flask.jsonify({'status': StatusCodes['success'], 'results': results})
  except (Exception, psycopg2.DatabaseError) as error:
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response