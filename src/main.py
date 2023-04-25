## Authors:
##  André Louro
##  Filipe Rodrigues
##  Joás Silva

# TODO: add boolean to consumer table (default: false)

import os
from dotenv import load_dotenv
load_dotenv()

import flask
import logging
import psycopg2
import time

import jwt

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
# params: {username, password, name, address, birthdate}
# return: user id if success
#? Create a Artist
# params: {username, password, name, address, birthdate, label_id, artistic_name)
# header: admin authentication token
# return: user id if success
#? Login a user
# params: {username, password}
# return: authentication token if success
@app.route('/dbproj/user', methods=['POST'])
def create_user():
  logger.info('POST /dbproj/user')
  payload = flask.request.get_json()

  conn = db_connection()
  cur = conn.cursor()

  logger.debug(f'POST /departments - payload: {payload}')

  if 'username' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username not provided'})
  if 'password' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'password not provided'})

  if 'name' not in payload and 'address' not in payload and 'birthdate' not in payload:
    #TODO: Login
    try:
      response = flask.jsonify({'status': StatusCodes['api_error'], 'results': 'not implemented'})
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
    if 'birthdate' not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'birthdate not provided'})
    
    if 'label_id' not in payload and 'artistic_name' not in payload:
      #TODO: Create a consumer
      try:
        response = flask.jsonify({'status': StatusCodes['api_error'], 'results': 'not implemented'})
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
      
      #TODO: Create a artist
      try:
        response = flask.jsonify({'status': StatusCodes['api_error'], 'results': 'not implemented'})
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