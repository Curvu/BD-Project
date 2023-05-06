from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
create_album = Blueprint('album', __name__)

# logger
logger = logging.getLogger('api')

#! POST http://localhost:8080/dbproj/album
'''
  headers = {
    token: authentication token (artist)
  }
  payload = {
    'title': string,
    'release_date': 'YYYY-MM-DD',
    'label_id': 'label_id',
    'other_artists': ['artist_id1', 'artist_id2', ...] (optional)
    'songs': [
      {'title': string, 'release_date': 'YYYY-MM-DD', 'duration': 'HH:MM:SS', 'genre': 'genre', 'label_id': 'label_id', 'other_artists': ['artist_id1', 'artist_id2', ...]},
      song_id2,
      ...
    ]
  }
  return: {
    'status': status_code,
    'results': album_id if success, 
    'error': error_message if any
  }
'''
@create_album.route('/', methods=['POST'])
def album():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  for field in ['title', 'release_date', 'label_id', 'songs']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})

  #* Check if token is valid *#
  jwt_decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

    #* Check if user is an artist *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM artist WHERE id = %s", (user_id, ))
    results = cur.fetchone()
    if results is None: # user is not an artist
      logger.info(f'User {user_id} is not an artist')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an artist'})
    else:
      logger.debug(f'User {user_id} is an artist')

      #* Create album *#
      values = (payload['title'], payload['release_date'], payload['label_id'])
      cur.execute("INSERT INTO album (title, release_date, label_id) VALUES (%s, %s, %s) RETURNING id", values)
      album_id = cur.fetchone()[0]
      logger.info(f'Album {album_id} created')
      response = flask.jsonify({'status': StatusCodes['success'], 'results': album_id})

      #* Add artists *#
      # associate with artist from token
      cur.execute("INSERT INTO album_artist (album_id, artist_id) VALUES (%s, %s)", (album_id, user_id))
      logger.debug(f'Artist {user_id} added to album {album_id}')

      # associate with artists from payload
      if 'other_artists' in payload:
        for artist_id in payload['other_artists']:
          cur.execute("INSERT INTO album_artist (album_id, artist_id) VALUES (%s, %s)", (album_id, artist_id))
          logger.debug(f'Artist {artist_id} added to album {album_id}')

      #* Add songs *#
      for i in range(len(payload['songs'])):
        if payload['songs'][i] is dict:
          # check this song has all fields provided
          song = payload['songs'][i]
          if 'title' not in song or 'release_date' not in song or 'duration' not in song or 'genre' not in song or 'label_id' not in song:
            logger.info(f'Song does not have all fields provided')
            continue
          # check this song exists
          cur.execute("SELECT ismn FROM song WHERE title = %s AND release_date = %s AND duration = %s AND genre = %s AND label_id = %s", (song['title'], song['release_date'], song['duration'], song['genre'], song['label_id']))
          results = cur.fetchone() # this should be the ismn
          if results is None:
            logger.info(f'Song does not exist')
            continue
          # check if the artists are associated with the song
          cur.execute("SELECT * FROM song_artist WHERE song_ismn = %s AND artist_id = %s", (results[0], user_id))
          results = cur.fetchone()
          if results is None:
            logger.info(f'Song does not have artist {user_id}')
            continue

          if 'other_artists' in song:
            for artist_id in song['other_artists']:
              cur.execute("SELECT * FROM song_artist WHERE song_ismn = %s AND artist_id = %s", (results[0], artist_id))
              results = cur.fetchone()
              if results is None:
                logger.info(f'Song does not have artist {artist_id}')
                continue
          # song matches all parameters and artists
          song_id = results[0]
          logger.debug(f'Song {song_id} exists')
        else:
          song_id = payload['songs'][i]
          # check this song exists
          cur.execute("SELECT * FROM song WHERE ismn = %s", (song_id, ))
          if cur.fetchone() is None:
            logger.info(f'Song {song_id} does not exist')
            continue

          # check if this song has the token artist
          cur.execute("SELECT * FROM song_artist WHERE song_ismn = %s AND artist_id = %s", (song_id, user_id))
          if cur.fetchone() is None:
            logger.info(f'Song {song_id} does not have artist {user_id}')
            continue

        # associate with song
        cur.execute("INSERT album_song (album_id, song_ismn) VALUES (%s, %s)", (album_id, song_id))
        logger.debug(f'Song {song_id} added to album {album_id}')
      conn.commit()
      response = flask.jsonify({'status': StatusCodes['success'], 'results': album_id})
  except (Exception, psycopg2.DatabaseError) as error:
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response