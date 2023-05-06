## Authors:
##  André Louro
##  Filipe Rodrigues
##  Joás Silva

from database import Database, StatusCodes, SecretKey

import flask
import logging
import psycopg2
import jwt
import os
from dotenv import load_dotenv
load_dotenv()

# import endpoints
from endpoints.register_user import register_user
from endpoints.login_user import login_user
from endpoints.create_song import create_song
from endpoints.get_song_keyword import get_song_keyword


app = flask.Flask(__name__)
app.config['DEBUG'] = True

app.register_blueprint(register_user, url_prefix='/dbproj/user')
app.register_blueprint(login_user, url_prefix='/dbproj/user')
app.register_blueprint(create_song, url_prefix='/dbproj/song')
app.register_blueprint(get_song_keyword, url_prefix='/dbproj/song')


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
  conn = Database().connect()
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


#! POST http://localhost:8080/dbproj/label
'''
  headers = {
    token: authentication token (admin)
  }
  payload = {
    'name': 'string',
    'contact': 'string',
  }
  return: {
    'status': status_code,
    'results': label_id if success,
    'error': error_message if any
  }
'''
@app.route('/dbproj/label', methods=['POST'])
def create_label():
  token = flask.request.headers.get('token')
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  payload = flask.request.get_json()
  if payload is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'payload not provided'})
  if 'name' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'name not provided'})
  if 'contact' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'contact not provided'})
  
  #* Check if token is valid *#
  jwt.decode(token, SecretKey, algorithms=['HS256'])
  admin_id = jwt.decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'Admin {admin_id} creating label')

    #* Check if user is an admin *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM administrator WHERE id = %s", (admin_id, ))
    if cur.fetchone() is None:
      logger.info(f'User {admin_id} is not an Admin')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an Admin'})
    else:
      logger.debug(f'User {admin_id} is an Admin')
      #* Create label *#
      query = '''
        INSERT INTO label (name, contact)
        VALUES (%s, %s)
        RETURNING id
      '''
      cur.execute(query, (payload['name'], payload['contact']))
      label_id = cur.fetchone()[0]
      conn.commit()
      logger.info(f'Label {label_id} created')
      response = flask.jsonify({'status': StatusCodes['success'], 'results': label_id})
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
  # create logger
  logging.basicConfig(filename='log_file.log')
  logger = logging.getLogger('api')
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