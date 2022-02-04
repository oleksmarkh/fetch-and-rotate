# import sys
from configparser import ConfigParser
from pathlib import PurePath
import datetime
import logging


# config
config_parser = ConfigParser()
config_parser.read('config.ini')
config = config_parser['DEFAULT']
log_dirname = config['log_dirname']
request_timeout = config.getint('request_timeout')
user_agent = config['user_agent']

# logging
logging.basicConfig(
  format='%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s',
  level=logging.DEBUG,
  handlers=[
    logging.StreamHandler(),
    logging.FileHandler(PurePath(
      log_dirname,
      f"{datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S')}.log"
    ))
  ]
)

if __name__ == '__main__':
  logging.info('start')
