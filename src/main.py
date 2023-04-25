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

###################################################
#               DATABASE CONNECTION               #
###################################################

def db_connection():
  return psycopg2.connect(
    user=os.getenv('USER'),
    password=os.getenv('PASSWORD'),
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
  return (
    """
      Hello World!
    """
  )

#* POST http://localhost:8080/dbproj/user
#? Create a consumer
# params: {username, password, name, address, email, birthdate}
# return: user id if success
#? Create a Artist
# params: {username, password, name, address, email, birthdate, label_id, artistic_name)
# header: admin authentication token
# return: user id if success
#? Login a user
# params: {username, password}
# return: authentication token if success
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
        response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user not found'})
      else:
        if bcrypt.checkpw(payload['password'].encode('utf-8'), results[2].encode('utf-8')):
          token = jwt.encode({'id': results[0]}, os.getenv('SECRET_KEY'), algorithm='HS256')
          response = flask.jsonify({'status': StatusCodes['success'], 'results': token.decode('utf-8')})
        else:
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
    hash = bcrypt.hashpw(payload['password'].encode('utf-8'), bcrypt.gensalt()) # hashed password
    if 'label_id' not in payload and 'artistic_name' not in payload:
      #* Consumer *#
      try:
        cur.execute("SELECT * FROM credentials WHERE username = %s", (payload['username'], ))
        results = cur.fetchone() # returns (id, username, password)
        if results is not None:
          response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username already in use'})
        else:
          cur.execute("INSERT INTO credentials (username, password) VALUES (%s, %s) RETURNING id", (payload['username'], hash))
          user_id = cur.fetchone()[0]
          values = (user_id, payload['name'], payload['address'], payload['email'], payload['birthdate'])
          cur.execute("INSERT INTO person (id, name, address, email, birthdate) VALUES (%s, %s, %s, %s, %s)", values)
          cur.execute("INSERT INTO consumer (id) VALUES (%s)", (user_id, ))
          conn.commit()
          response = flask.jsonify({'status': StatusCodes['success'], 'results': user_id})
      except (Exception, psycopg2.DatabaseError) as error:
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
          response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username already in use'})
        else:
          cur.execute("INSERT INTO credentials (username, password) VALUES (%s, %s) RETURNING id", (payload['username'], hash))
          user_id = cur.fetchone()[0]
          values = (user_id, payload['name'], payload['address'], payload['email'], payload['birthdate'])
          cur.execute("INSERT INTO person (id, name, address, email, birthdate) VALUES (%s, %s, %s, %s, %s)", values)
          values = (user_id, payload['label_id'], payload['artistic_name'])
          cur.execute("INSERT INTO artist (id, label_id, artistic_name) VALUES (%s, %s, %s)", values)
          conn.commit()
          response = flask.jsonify({'status': StatusCodes['success'], 'results': user_id})
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