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
        SELECT song.ismn, song.title, song.label_id, artist.artistic_name, album.id
        FROM song
        LEFT JOIN song_artist ON song.ismn = song_artist.song_ismn
        LEFT JOIN artist      ON song_artist.artist_id = artist.id
        LEFT JOIN album_song  ON song.ismn = album_song.song_ismn
        LEFT JOIN album       ON album_song.album_id = album.id
        WHERE song.title LIKE %s
        GROUP BY song.ismn, artist.artistic_name, album.id
      '''
      cur.execute(query, (value, ))
      results = cur.fetchall()
      songs = {}
      for result in results:
        ismn, title, label_id, artist_name, album_id = result
        if ismn not in songs: # if the song is not in the dictionary 'songs'
          songs[ismn] = { 'title': title, 'label': label_id, 'artists': [artist_name], 'albums': [album_id] }
        else: # if the song is in the dictionary 'songs'
          if artist_name not in songs[ismn]['artists']:
            songs[ismn]['artists'].append(artist_name)
          if album_id not in songs[ismn]['albums']:
            songs[ismn]['albums'].append(album_id)
      response = flask.jsonify({'status': StatusCodes['success'], 'results': list(songs.values())})
  except (Exception, psycopg2.DatabaseError) as error:
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response
