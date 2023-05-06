import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

StatusCodes = {
  'success': 200,
  'api_error': 400,
  'internal_error': 500
}

SecretKey = os.getenv('SECRET_KEY')


###################################################
#               DATABASE CONNECTION               #
###################################################

class Database:
  def __init__(self):
    self.user = os.getenv('DB_USER')
    self.password = os.getenv('DB_PASSWORD')
    self.host = os.getenv('HOST')
    self.port = os.getenv('DB_PORT')
    self.dbname = os.getenv('DATABASE')

  def connect(self):
    try:
      return psycopg2.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.dbname)
    except (Exception, psycopg2.DatabaseError) as error:
      return None