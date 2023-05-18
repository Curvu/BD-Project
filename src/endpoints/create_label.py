from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
create_label = Blueprint('label', __name__)

# logger
logger = logging.getLogger('api')

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
@create_label.route('/', methods=['POST'])
def label():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})

  for field in ['name', 'contact']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})

  #* Check if token is valid *#
  admin_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
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

      # lock label table for insertion but allow reading
      cur.execute('LOCK TABLE label IN ACCESS EXCLUSIVE MODE')

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
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response
