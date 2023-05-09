from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
create_playlist = Blueprint('playlist', __name__)

# logger
logger = logging.getLogger('api')

visibilidade = {
  'public': False,
  'private': True
}

#! POST http://localhost:8080/dbproj/playlist
'''
  headers = {
    token: authentication token (consumer)
  }
  payload = {
    'playlist_name': string,
    'visibility': 'public' or 'private',
    'songs': [song_id1, song_id2, ... ]
  }
  return: {
    'status': status_code,
    'results': playlist_id, 
    'error': error_message
  }
'''
@create_playlist.route('/', methods=['POST'])
def playlist():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  for field in ['playlist_name', 'visibility', 'songs']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})

  #* Check if token is valid *#
  jwt_decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an consumer and has a subscription ongoing *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    query = '''
      SELECT consumer.id
      FROM consumer
      LEFT JOIN consumer_subscription ON consumer.id = consumer_subscription.consumer_id
      LEFT JOIN subscription ON consumer_subscription.subscription_id = subscription.id
      WHERE subscription.end_date > NOW() AND subscription.start_date < NOW() AND consumer.id = %s
    '''
    cur.execute(query, (user_id, ))

    if cur.fetchone() is None: # user in not an consumer or has no subscription
      logger.info(f'User {user_id} is not a consumer or does not have a subscription')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not a consumer or does not have a subscription'})
    else: 
      logger.debug(f'User {user_id} is a consumer and has a subscription ongoing')

      #* Create playlist *#
      cur.execute("INSERT INTO playlist (name, private) VALUES (%s, %s) RETURNING id", (payload['playlist_name'], visibilidade[payload['visibility']]))
      playlist_id = cur.fetchone()[0]
      logger.debug(f'Playlist {playlist_id} created')

      #* Associate playlist with consumer *#
      cur.execute("INSERT INTO consumer_playlist (consumer_id, playlist_id) VALUES (%s, %s)", (user_id, playlist_id))
      logger.debug(f'Playlist {playlist_id} associated with consumer {user_id}')

      #* Add songs to playlist *#
      for song_id in payload['songs']:
        cur.execute("INSERT INTO song_playlist (playlist_id, song_ismn) VALUES (%s, %s)", (playlist_id, song_id))
        logger.debug(f'Song {song_id} added to playlist {playlist_id}')
      conn.commit()
      response = flask.jsonify({'status': StatusCodes['success'], 'results': playlist_id})
      logger.info(f'Playlist {playlist_id} created')
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response