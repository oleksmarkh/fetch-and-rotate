# import sys
from configparser import ConfigParser, SectionProxy
from pathlib import PurePath
import datetime
import logging


def read_config(filename: str) -> SectionProxy:
  config_parser = ConfigParser()
  config_parser.read(filename)
  return config_parser['DEFAULT']


def init_logging(dirname: str, filename_datetime_format: str) -> None:
  filename = f"{datetime.datetime.now().strftime(filename_datetime_format)}.log"
  logging.basicConfig(
    format='%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s',
    level=logging.DEBUG,
    handlers=[
      logging.StreamHandler(),
      logging.FileHandler(PurePath(dirname, filename))
    ]
  )


def read_webpage_list(filename: str) -> list[str]:
  with open(filename) as file:
    return file.read().splitlines()


if __name__ == '__main__':
  config = read_config('config.ini')
  # request_timeout = config.getint('request_timeout')
  # user_agent = config['user_agent']
  init_logging(config['log_dirname'], '%Y-%m-%d--%H-%M-%S')
  webpage_list = read_webpage_list(config['input_filename'])
  logging.info(f"List of webpages ({len(webpage_list)}): {webpage_list}")
