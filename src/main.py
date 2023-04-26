## Authors:
##  André Louro
##  Filipe Rodrigues
##  Joás Silva

import flask
import logging
import psycopg2
import jwt
import bcrypt
import os
from dotenv import load_dotenv
load_dotenv()

app = flask.Flask(__name__)

StatusCodes = {
  'success': 200,
  'api_error': 400,
  'internal_error': 500
}

SecretKey = os.getenv('SECRET_KEY')

###################################################
#               DATABASE CONNECTION               #
###################################################

def db_connection():
  return psycopg2.connect(
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DATABASE')
  )


###################################################
#               ENDPOINTS DEFINITION              #
###################################################

# Example endpoint default
@app.route('/')
def landing_page():
  logger.info('GET /')
  return (
    """
      Hello World!
    """
  )


#! POST http://localhost:8080/dbproj/user
'''
  payload: {
    username: string,
    password: string,
    name: string, (optional if login)
    address: string, (optional if login)
    email: string, (optional if login)
    birthdate: string, (optional if login)
    label_id: int, (optional if login and not artist)
    artistic_name: string (optional if login and not artist)
  }
  return: {
    status: status code,
    results: user_id if register or token if login,
    error: error message if error
  }
'''
@app.route('/dbproj/user', methods=['POST'])
def create_login_user():
  logger.info('POST /dbproj/user')
  payload = flask.request.get_json()

  conn = db_connection()
  cur = conn.cursor()

  logger.debug(f'POST /departments - payload: {payload}')

  if 'username' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username not provided'})
  if 'password' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'password not provided'})

  if 'name' not in payload and 'address' not in payload and 'birthdate' not in payload and 'email' not in payload:
    #* Login *#
    try:
      cur.execute("SELECT * FROM credentials WHERE username = %s", (payload['username'], ))
      results = cur.fetchone() # returns (id, username, password)
      if results is None:
        logger.info(f'User {payload["username"]} not found')
        response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user not found'})
      else:
        pw = results[2].encode('utf-8')
        if bcrypt.checkpw(payload['password'].encode('utf-8'), pw):
          logger.info(f'User {results[0]} logged in')
          token = jwt.encode({'user_id': results[0]}, SecretKey, algorithm='HS256')
          response = flask.jsonify({'status': StatusCodes['success'], 'results': token})
        else:
          logger.info(f'User {results[0]} failed to login')
          response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'wrong password'})
    except (Exception, psycopg2.DatabaseError) as error:
      logger.error(str(error))
      response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
    finally:
      if conn is not None:
        conn.close()
      return response
  else:
    if 'name' not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'name not provided'})
    if 'address' not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'address not provided'})
    if 'email' not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'email not provided'})
    if 'birthdate' not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'birthdate not provided'})
    
    #* Create a user *#
    hash = bcrypt.hashpw(payload['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    if 'label_id' not in payload and 'artistic_name' not in payload:
      #* Consumer *#
      try:
        cur.execute("SELECT * FROM credentials WHERE username = %s", (payload['username'], ))
        results = cur.fetchone() # returns (id, username, password)
        if results is not None:
          logger.info(f'Username {payload["username"]} already in use')
          response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username already in use'})
        else:
          cur.execute("INSERT INTO credentials (username, password) VALUES (%s, %s) RETURNING id", (payload['username'], hash))
          user_id = cur.fetchone()[0]
          values = (user_id, payload['name'], payload['address'], payload['email'], payload['birthdate'])
          cur.execute("INSERT INTO person (id, name, address, email, birthdate) VALUES (%s, %s, %s, %s, %s)", values)
          cur.execute("INSERT INTO consumer (id) VALUES (%s)", (user_id, ))
          conn.commit()
          logger.info(f'User {user_id} created')
          response = flask.jsonify({'status': StatusCodes['success'], 'results': user_id})
      except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        logger.error(str(error))
        response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
      finally:
        if conn is not None:
          conn.close()
        return response
    else:
      if 'label_id' not in payload:
        return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'label_id not provided'})
      if 'artistic_name' not in payload:
        return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'artistic_name not provided'})
      
      #* Artist *#
      try:
        cur.execute("SELECT * FROM credentials WHERE username = %s", (payload['username'], ))
        results = cur.fetchone() # returns (id, username, password)
        if results is not None:
          logger.info(f'Username {payload["username"]} already in use')
          response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username already in use'})
        else:
          cur.execute("INSERT INTO credentials (username, password) VALUES (%s, %s) RETURNING id", (payload['username'], hash))
          user_id = cur.fetchone()[0]
          values = (user_id, payload['name'], payload['address'], payload['email'], payload['birthdate'])
          cur.execute("INSERT INTO person (id, name, address, email, birthdate) VALUES (%s, %s, %s, %s, %s)", values)
          values = (user_id, payload['label_id'], payload['artistic_name'])
          cur.execute("INSERT INTO artist (id, label_id, artistic_name) VALUES (%s, %s, %s)", values)
          conn.commit()
          logger.info(f'User {user_id} created')
          response = flask.jsonify({'status': StatusCodes['success'], 'results': user_id})
      except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        logger.error(str(error))
        response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
      finally:
        if conn is not None:
          conn.close()
        return response


#! POST http://localhost:8080/dbproj/song
'''
  headers = {
    token: authentication token (artist)
  }
  payload = {
    'title': string,
    'release_date': 'YYYY-MM-DD',
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
@app.route('/dbproj/song', methods=['POST'])
def create_song():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  if 'title' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'title not provided'})
  if 'release_date' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'release_date not provided'})
  if 'duration' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'duration not provided'})
  if 'genre' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'genre not provided'})
  if 'label_id' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'label_id not provided'})

  #* Check if token is valid *#
  jwt.decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt.decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an artist *#
  conn = db_connection()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM artist WHERE id = %s", (user_id, ))
    results = cur.fetchone()
    if results is None:
      logger.info(f'User {user_id} is not an artist')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an artist'})
    else:
      logger.debug(f'User {user_id} is an artist')

      #* Create song *#
      values = (payload['title'], payload['release_date'], payload['duration'], payload['genre'], payload['label_id'])
      cur.execute("INSERT INTO song (title, release_date, duration, genre, label_id, album_id) VALUES (%s, %s, %s, %s, %s) RETURNING ismn", values)
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
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response


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
@app.route('/dbproj/album', methods=['POST'])
def create_album():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  if 'title' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'title not provided'})
  if 'release_date' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'release_date not provided'})
  if 'label_id' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'label_id not provided'})
  if 'songs' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'songs not provided'})

  #* Check if token is valid *#
  jwt.decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt.decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

    #* Check if user is an artist *#
  conn = db_connection()
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
@app.route('/dbproj/song/<keyword>', methods=['GET'])
def get_song(keyword):
  token = flask.request.headers.get('token')
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})

  #* Check if token is valid *#
  jwt.decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt.decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an Consumer *#
  conn = db_connection()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM consumer WHERE id = %s", (user_id, ))
    if cur.fetchone() is None:
      logger.info(f'User {user_id} is not an Consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an Consumer'})
    else:
      logger.debug(f'User {user_id} is an Consumer')
      #* Get songs *#
      value = '%' + keyword + '%'
      # check title, genre, artist_name, album_name
      query = '''
        SELECT song.ismn, song.title, artist.artistic_name, album.id
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
        ismn, title, artist_name, album_id = result
        if ismn not in songs: # if the song is not in the dictionary 'songs'
          songs[ismn] = { 'title': title, 'artists': [artist_name], 'albums': [album_id] }
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


#! GET http://localhost:8080/dbproj/artist_info/{artist_id}
'''
  header: {
    token: auth token (consumer)
  }
  return: {
    'status': status_code,
    'results': [
      {'name': artist_name, 'songs': [song_id, ...], 'albums': [album_id, ...], 'playlists': [playlist_id, ...]},
      ...
    ]
    'error': error message
'''
@app.route('/dbproj/artist_info/<artist_id>', methods=['GET'])
def get_artist_info(artist_id):
  token = flask.request.headers.get('token')
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})

  #* Check if token is valid *#
  jwt.decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt.decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an Consumer *#
  conn = db_connection()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM consumer WHERE id = %s", (user_id, ))
    if cur.fetchone() is None:
      logger.info(f'User {user_id} is not an Consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an Consumer'})
    else:
      logger.debug(f'User {user_id} is an Consumer')
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



###################################################
#                     MAIN                        #
###################################################

if __name__ == '__main__':
  # set up logging
  logging.basicConfig(filename='log_file.log')
  logger = logging.getLogger('logger')
  logger.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)

  # create formatter
  formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
  ch.setFormatter(formatter)
  logger.addHandler(ch)

  host = os.getenv('HOST')
  port = os.getenv('API_PORT')
  app.run(host=host, debug=True, threaded=True, port=port)
  logger.info(f'API v1.0 online: http://{host}:{port}')