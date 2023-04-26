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
    'artists': ['artist_id1', 'artist_id2', ...] (optional)
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
  if payload is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'payload not provided'})

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
      try:
        values = (payload['title'], payload['release_date'], payload['duration'], payload['genre'], payload['label_id'])
        cur.execute("INSERT INTO song (title, release_date, duration, genre, label_id, album_id) VALUES (%s, %s, %s, %s, %s) RETURNING id", values)
        song_id = cur.fetchone()[0]
        logger.info(f'Song {song_id} created')
        response = flask.jsonify({'status': StatusCodes['success'], 'results': song_id})

        #* Add artists *#
        # associate with artist from token
        cur.execute("INSERT INTO song_artist (song_id, artist_id) VALUES (%s, %s)", (song_id, user_id))
        logger.debug(f'Artist {user_id} added to song {song_id}')

        # associate with artists from payload
        if 'artists' in payload:
          for artist_id in payload['artists']:
            cur.execute("INSERT INTO song_artist (song_id, artist_id) VALUES (%s, %s)", (song_id, artist_id))
            logger.debug(f'Artist {artist_id} added to song {song_id}')
        conn.commit()
      except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        logger.error(str(error))
        response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
      finally:
        if conn is not None:
          conn.close()
        return response
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