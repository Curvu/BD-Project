from database import Database, StatusCodes, SecretKey

import logging
import flask
from flask import Blueprint
import psycopg2
from jwt import decode as jwt_decode

# blueprint
month_report = Blueprint('report', __name__)

# logger
logger = logging.getLogger('api')

#! GET http://localhost:8080/dbproj/report/{year-month}
'''
  header: {
    token: auth token (consumer)
  }
  return: {
    status: status code,
    results: [
      {“month”: “month_0”, “genre”: “genre1”, “playbacks”: total_songs_played},
      ...
    ],
    error: error message
  }
'''
@month_report.route('/<year_month>', methods=['GET']) # year_month = 'YYYY-MM'
def report(year_month):
  token = flask.request.headers.get('token')
  if token is None:
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'token not provided'})

  # if YYYY-MM or YYYY-M
  if (len(year_month) != 7 and len(year_month) != 6) or year_month[4] != '-' or not year_month[:4].isdigit() or not year_month[5:].isdigit():
    return flask.jsonify({'status': StatusCodes['api_error'], 'error': 'invalid year-month format'})

  # append '-01' to year_month (first day of the month)
  year_month += '-01'


  #* Check if token is valid *#
  user_id = jwt_decode(token, SecretKey, algorithms=['HS256'])['user_id']
  logger.debug(f'User {user_id} authenticated')

  #* Check if user is a consumer *#
  conn = Database().connect()
  cur = conn.cursor()

  try:
    cur.execute("SELECT id FROM consumer WHERE id = %s", (user_id, ))
    results = cur.fetchone()
    if results is None:
      logger.info(f'User {user_id} is not a consumer')
      response = flask.jsonify({'status': StatusCodes['api_error'], 'error': 'user is not a consumer'})
    else:
      logger.debug(f'User {user_id} is a consumer')

      # song listen date (YYYY-MM-DD) >= 'YYYY-MM' - 12 months AND song listen date <= year_month

      query = '''
        SELECT COUNT(consumer_song.song_ismn), song.genre, EXTRACT(MONTH FROM consumer_song.listen_date) as month
        FROM consumer_song
        LEFT JOIN song ON consumer_song.song_ismn = song.ismn
        WHERE
          consumer_song.consumer_id = %s
          AND consumer_song.listen_date >= %s::date - INTERVAL '12 months'
          AND consumer_song.listen_date <= %s::date + INTERVAL '1 months'
        GROUP BY song.genre, month
        ORDER BY month, COUNT(consumer_song.song_ismn) DESC;
      '''
      cur.execute(query, (user_id, year_month, year_month))
      results = cur.fetchall()
      response = flask.jsonify({'status': StatusCodes['success'], 'results': results})
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
