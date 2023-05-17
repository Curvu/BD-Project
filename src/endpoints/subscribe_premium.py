from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode
from datetime import datetime, timedelta

# blueprint
subscribe_premium = Blueprint('subscribe', __name__)

# logger
logger = logging.getLogger('api')

valid_period = {
  'month': [30, 7], # days, price
  'quarter': [90, 21],
  'semester': [105, 42]
}

#! POST http://localhost:8080/dbproj/subscription
'''
  headers = {
    token: authentication token (consumer)
  }
  payload = {
    'period': 'month' or 'quarter' or 'semester',
    'cards': [card_id1, card_id2, ...]
  }
  return: {
    'status': status_code,
    'results': subscription_id,
    'error': error_message
  }
'''
@subscribe_premium.route('/', methods=['POST'])
def subscribe():
  token = flask.request.headers.get('token')
  payload = flask.request.get_json()
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})
  
  for field in ['period', 'cards']:
    if field not in payload:
      return flask.jsonify({'status': StatusCodes['api_error'], 'error': f'{field} not provided'})
  if payload['period'] not in valid_period:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'invalid period'})

  #* Check if token is valid *#
  jwt_decode(token, SecretKey, algorithms=['HS256'])
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is an consumer *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute("SELECT * FROM consumer WHERE id = %s", (user_id, ))
    results = cur.fetchone()
    if results is None:
      logger.info(f'User {user_id} is not a consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not a consumer'})
    else:
      logger.debug(f'User {user_id} is a consumer')

      #* Create transaction *#
      cur.execute('INSERT INTO transaction (transaction_date) VALUES (NOW()) RETURNING id')
      transaction_id = cur.fetchone()[0]

      #* Check if user has a subscription ongoing *#
      cur.execute('''
        SELECT consumer_subscription.consumer_id, subscription.end_date
        FROM consumer_subscription
        LEFT JOIN subscription ON consumer_subscription.subscription_id = subscription.id
        WHERE consumer_id = %s AND subscription.end_date > CURRENT_DATE
      ''', (user_id, ))

      results = cur.fetchone()
      start_date = None
      if results is not None: # user has a subscription ongoing
        logger.info(f'User {user_id} has a subscription ongoing')
        # get the last subscription end date
        query = '''
          SELECT subscription.end_date
          FROM consumer_subscription
          LEFT JOIN subscription ON consumer_subscription.subscription_id = subscription.id
          WHERE consumer_id = %s
          ORDER BY subscription.end_date DESC
        '''
        cur.execute(query, (user_id, ))
        # start new subscription after the current one ends
        start_date = cur.fetchone()[0] + timedelta(days=1)
      else: # user has no subscription ongoing
        logger.debug(f'User {user_id} has no subscription ongoing')
        start_date = datetime.now().date()
      end_date = start_date + timedelta(days=valid_period[payload['period']][0])
      cur.execute('INSERT INTO subscription (plan, start_date, end_date, t_id) VALUES (%s, %s, %s, %s) RETURNING id', (payload['period'], start_date, end_date, transaction_id))
      subscription_id = cur.fetchone()[0]
      cur.execute('INSERT INTO consumer_subscription (consumer_id, subscription_id) VALUES (%s, %s)', (user_id, subscription_id))
      response = flask.jsonify({'status': StatusCodes['success'], 'results': subscription_id})

      #* Check if the balance of the cards is enough to pay for the subscription *#
      price = valid_period[payload['period']][1]
      for card_id in payload['cards']:
        cur.execute('SELECT amount, consumer_id FROM prepaid_card WHERE id = %s', (card_id, ))
        balance, consumer_id = cur.fetchone()
        if (consumer_id is None):
          cur.execute('UPDATE prepaid_card SET consumer_id = %s WHERE id = %s RETURNING consumer_id', (user_id, card_id))
          consumer_id = cur.fetchone()[0]
        if balance is not None and consumer_id == user_id: # card belongs to user
          # remove until the balance is 0
          used = 0
          while balance > 0:
            price -= 1
            balance -= 1
            used += 1
            if balance == 0 or price == 0:
              cur.execute('INSERT INTO transaction_prepaid_card (ppc_id, t_id, amount) VALUES (%s, %s, %s)', (card_id, subscription_id, used))
              break
          # update card balance and card
          cur.execute('UPDATE prepaid_card SET amount = %s WHERE id = %s', (balance, card_id))
          if price == 0:
            break
      if price > 0:
        print(price, balance)
        conn.rollback()
        logger.info(f'Not enough balance in cards')
        response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'not enough balance in cards'})
      else:
        conn.commit()
        response = flask.jsonify({'status': StatusCodes['success'], 'results': subscription_id})
  except (Exception, psycopg2.DatabaseError) as error:
    if conn is not None:
      conn.rollback()
    logger.error(str(error))
    response = flask.jsonify({'status': StatusCodes['internal_error'], 'error': str(error)})
  finally:
    if conn is not None:
      conn.close()
    return response
