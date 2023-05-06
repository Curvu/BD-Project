from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode
import random
import string

# blueprint
generate_ppc = Blueprint('generate', __name__)

# logger
logger = logging.getLogger('api')

valid_cards = [10, 25, 50]

def generate_id():
  # generate a string with 16 random digits a-zA-Z0-9
  return ''.join(random.choices(string.ascii_letters + string.digits, k=16)).upper()

#! POST http://localhost:8080/dbproj/card
'''
  headers = {
    token: authentication token (admin)
  }
  payload = {
    'number_cards': 'number' (number of cards to generate),
    'card_price': 10, 25 or 50
  }
  return: {
    'status': status_code,
    'results': [card_id1, card_id2, ...],
    'error': error_message
  }
'''
@generate_ppc.route('/', methods=['POST'])
def generate():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  for field in ['number_cards', 'card_price']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})

  #* Check if token is valid *#
  jwt_decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an amdin *#
  conn = Database().connect()
  cur = conn.cursor()

  cards = []
  try:
    cur.execute('SELECT id FROM administrator WHERE id = %s', (user_id, ))

    if cur.fetchone() is None: # user in not an admin
      logger.info(f'User {user_id} is not an admin')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not an admin'})
    else: 
      logger.debug(f'User {user_id} is an amdin')

      if payload['card_price'] in valid_cards:
        logger.debug(f'Card price is valid')
        for i in range(payload['number_cards']):
          #* generate card *#
          # expire = CURRENT_DATE + 1 year
          cur.execute('INSERT INTO prepaid_card (id, amount, admin_id, expire) VALUES (%s, %s, %s, CURRENT_DATE + INTERVAL \'1 year\') RETURNING id', (generate_id(), payload['card_price'], user_id))
          cards.append(cur.fetchone()[0])

      conn.commit()
      response = flask.jsonify({'status': StatusCodes['success'], 'results': cards})
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response