from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
chain_comment = Blueprint('reply_comment', __name__)

# logger
logger = logging.getLogger('api')

#! POST http://localhost:8080/dbproj/comments/{song_id}/{parent_comment_id}
'''
  headers = {
    token: authentication token (consumer)
  }
  payload = {
    'comment': 'string'
  }
  return: {
    'status': status_code,
    'results': comment_id,
    'error': error_message
  }
'''
@chain_comment.route('/<song_id>/<parent_comment_id>', methods=['POST'])
def reply_comment(song_id, parent_comment_id):
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  if payload['comment'] is None:
    return flask.jsonify({'status': StatusCodes['api_error', 'error': 'comment not provided']})

  #* Check if token is valid *#
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is a consumer *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute('SELECT id FROM consumer WHERE id = %s', (user_id, ))

    if cur.fetchone() is None: # user in not a consumer
      logger.info(f'User {user_id} is not a consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not a consumer'})
    else: # user is a consumer
      logger.debug(f'User {user_id} is a consumer')

      # block the parent comment so that no one can delete it while we are replying to it
      cur.execute('LOCK TABLE comment IN ACCESS EXCLUSIVE MODE')

      #* Create comment *#
      query = '''
        INSERT INTO comment (song_ismn, consumer_id, content, parent_id, comment_date)
        VALUES (%s, %s, %s, %s, NOW())
        RETURNING id
      '''
      cur.execute(query, (song_id, user_id, payload['comment'], parent_comment_id))
      comment_id = cur.fetchone()[0]

      logger.debug(f'User {user_id} left a comment on song {song_id}')
      response = flask.jsonify({'status': StatusCodes['success'], 'results': comment_id})
      conn.commit()
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response