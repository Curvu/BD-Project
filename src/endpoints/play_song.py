from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
play_song = Blueprint('play', __name__)

# logger
logger = logging.getLogger('api')

#TODO: implementar trigger para atualizar most listened user song playlist (top 10)

#! POST http://localhost:8080/dbproj/<song_id>
'''
  headers = {
    token: authentication token (consumer)
  }
  return: {
    'status': status_code,
    'error': error_message
  }
'''
@play_song.route('/<song_id>', methods=['PUT'])
def play(song_id):
  token = flask.request.headers.get('token')
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})

  #* Check if token is valid *#
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is a consumer *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute('SELECT consumer.id FROM consumer WHERE id = %s', (user_id, ))

    if cur.fetchone() is None: # user in not a consumer
      logger.info(f'User {user_id} is not a consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not a consumer'})
    else: 
      logger.debug(f'User {user_id} is a consumer')

      #* Update consumer_song *#
      # check if consumer_song has been played today
      cur.execute('SELECT * FROM consumer_song WHERE consumer_id = %s AND song_ismn = %s AND listen_date = CURRENT_DATE', (user_id, song_id))
      if cur.fetchone() is None: # consumer_song has not been played today
        logger.debug(f'Consumer {user_id} has not played song {song_id} today')
        # add the today's date to consumer_song
        cur.execute('INSERT INTO consumer_song (consumer_id, song_ismn, listen_date, views) VALUES (%s, %s, CURRENT_DATE, %s)', (user_id, song_id, 1))
      else: # consumer_song has been played today
        logger.debug(f'Consumer {user_id} has played song {song_id} today')
        # increment the views of consumer_song
        cur.execute('UPDATE consumer_song SET views = views + 1 WHERE consumer_id = %s AND song_ismn = %s AND listen_date = CURRENT_DATE', (user_id, song_id))
      conn.commit()
      response = flask.jsonify({'status': StatusCodes['success']})
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response