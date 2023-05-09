## Authors:
##  André Louro
##  Filipe Rodrigues
##  Joás Silva
import flask
import logging
import os
from dotenv import load_dotenv
load_dotenv()

app = flask.Flask(__name__)

###################################################
#               ENDPOINTS DEFINITION              #
###################################################
from endpoints.register_user import register_user
from endpoints.login_user import login_user
from endpoints.create_song import create_song
from endpoints.get_song_keyword import get_song_keyword
from endpoints.get_artist import get_artist
from endpoints.create_label import create_label
from endpoints.create_album import create_album
from endpoints.create_playlist import create_playlist
from endpoints.play_song import play_song
from endpoints.generate_ppc import generate_ppc
from endpoints.subscribe_premium import subscribe_premium
from endpoints.leave_comment import leave_comment
from endpoints.chain_comment import chain_comment


app.register_blueprint(register_user, url_prefix='/dbproj/user')
app.register_blueprint(login_user, url_prefix='/dbproj/user')
app.register_blueprint(create_song, url_prefix='/dbproj/song')
app.register_blueprint(get_song_keyword, url_prefix='/dbproj/song')
app.register_blueprint(get_artist, url_prefix='/dbproj/artist_info')
app.register_blueprint(create_label, url_prefix='/dbproj/label')
app.register_blueprint(create_album, url_prefix='/dbproj/album')
app.register_blueprint(create_playlist, url_prefix='/dbproj/playlist')
app.register_blueprint(play_song, url_prefix='/dbproj/')
app.register_blueprint(generate_ppc, url_prefix='/dbproj/card')
app.register_blueprint(subscribe_premium, url_prefix='/dbproj/subscription')
app.register_blueprint(leave_comment, url_prefix='/dbproj/comments/')
app.register_blueprint(chain_comment, url_prefix='/dbproj/comments/')

@app.route('/')
def landing_page():
  logger.info('GET /')
  return (
    """
      Hello World!
    """
  )

###################################################
#                     MAIN                        #
###################################################
if __name__ == '__main__':
  # create logger
  logging.basicConfig(filename='log_file.log')
  logger = logging.getLogger('api')
  logger.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  # create formatter
  formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
  ch.setFormatter(formatter)
  logger.addHandler(ch)

  host = os.getenv('HOST')
  port = os.getenv('API_PORT')
  app.run(host=host, debug=True, threaded=True, port=port)
  logger.info(f'API v1.0 online: http://{host}:{port}')