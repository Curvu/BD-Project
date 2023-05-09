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
        SELECT artist.artistic_name, song.ismn, album.id, playlist.id
        FROM artist
        LEFT JOIN song_artist   ON artist.id = song_artist.artist_id
        LEFT JOIN song          ON song_artist.song_ismn = song.ismn
        LEFT JOIN album_song    ON song.ismn = album_song.song_ismn
        LEFT JOIN album         ON album_song.album_id = album.id
        LEFT JOIN song_playlist ON song.ismn = song_playlist.song_ismn
        LEFT JOIN playlist      ON song_playlist.playlist_id = playlist.id
        WHERE artist.id = %s
      '''
      cur.execute(query, (artist_id, ))
      results = cur.fetchall()
      artist = {}
      for result in results:
        artist_name, song_id, album_id, playlist_id = result
        if artist_name not in artist:
          artist[artist_name] = { 'songs': [song_id], 'albums': [album_id], 'playlists': [playlist_id] }
        else:
          if song_id not in artist[artist_name]['songs']:
            artist[artist_name]['songs'].append(song_id)
          if album_id not in artist[artist_name]['albums']:
            artist[artist_name]['albums'].append(album_id)
          if playlist_id not in artist[artist_name]['playlists']:
            artist[artist_name]['playlists'].append(playlist_id)
      output = { 'name': artist_name, 'songs': artist[artist_name]['songs'], 'albums': artist[artist_name]['albums'], 'playlists': artist[artist_name]['playlists'] }
      response = flask.jsonify({'status': StatusCodes['success'], 'results': output})
  except (Exception, psycopg2.DatabaseError) as error:
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response