from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
import bcrypt
from jwt import encode as jwt_encode

# blueprint
login_user = Blueprint('login', __name__)

# logger
logger = logging.getLogger('api')

#! PUT http://localhost:8080/dbproj/user
'''
  payload: {
    username: string,
    password: string
  }
  return: {
    status: status code,
    results: token,
    error: error message
  }
'''
@login_user.route('/', methods=['PUT'])
def login():
  logger.info('PUT /dbproj/user')
  payload = flask.request.get_json()

  conn = Database().connect()
  cur = conn.cursor()

  logger.debug(f'PUT - payload: {payload}')

  if 'username' not in payload or 'password' not in payload:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'username or password not provided'})

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
        token = jwt_encode({'user_id': results[0]}, SecretKey, algorithm='HS256')
        response = flask.jsonify({'status': StatusCodes['success'], 'results': token})
      else:
        logger.info(f'User {results[0]} failed to login')
        response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'wrong password'})
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response
