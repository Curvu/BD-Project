from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
import bcrypt
from jwt import decode as jwt_decode

# blueprint
register_user = Blueprint('register', __name__)

# logger
logger = logging.getLogger('api')

#! POST http://localhost:8080/dbproj/user
'''
  header: {
    token: admin token (to register an artist)
  }
  payload: {
    username: string,
    password: string,
    name: string,
    address: string,
    email: string,
    birthdate: string,
    label_id: int, (optional if not artist)
    artistic_name: string (optional if not artist)
  }
  return: {
    status: status code,
    results: user_id,
    error: error message
  }
'''
@register_user.route('/', methods=['POST'])
def register():
  logger.info('POST /dbproj/user')
  payload = flask.request.get_json()

  conn = Database().connect()
  cur = conn.cursor()

  logger.debug(f'POST - payload: {payload}')

  for field in ['username', 'password', 'name', 'address', 'email', 'birthdate']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})

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
        # block credentials table for exclusive access 
        cur.execute("LOCK TABLE credentials, person IN ACCESS EXCLUSIVE MODE")

        cur.execute("INSERT INTO credentials (username, password) VALUES (%s, %s) RETURNING id", (payload['username'], hash))
        user_id = cur.fetchone()[0]
        values = (user_id, payload['name'], payload['address'], payload['email'], payload['birthdate'])
        cur.execute("INSERT INTO person (id, name, address, email, birthdate) VALUES (%s, %s, %s, %s, %s)", values)
        cur.execute("INSERT INTO consumer (id) VALUES (%s)", (user_id, ))
        conn.commit()
        logger.info(f'User {user_id} created')
        response = flask.jsonify({'status': StatusCodes['success'], 'results': user_id})
    except (Exception, psycopg2.DatabaseError) as error:
      if conn is not None:
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
    
    token = flask.request.headers.get('token')
    if token is None:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
    
    #* Check if token is valid *#
    admin_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
    #* Artist *#
    try:
      cur.execute("SELECT * FROM administrator WHERE id = %s", (admin_id, ))
      results = cur.fetchone()
      if results is None:
        logger.info(f'User {admin_id} is not an administrator')
        response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an administrator'})
      else:
        # block credentials table for exclusive access 
        cur.execute("LOCK TABLE credentials IN ACCESS EXCLUSIVE MODE")

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
      if conn is not None:
        conn.rollback()
      logger.error(str(error))
      response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
    finally:
      if conn is not None:
        conn.close()
      return response