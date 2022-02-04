# import sys
import asyncio
import datetime
import logging
from configparser import ConfigParser, SectionProxy
from pathlib import PurePath


def read_config(filename: str) -> SectionProxy:
  config_parser = ConfigParser()
  config_parser.read(filename)
  return config_parser['DEFAULT']


def config_logging(dirname: str, filename_datetime_format: str) -> None:
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


async def fetch_and_parse_img_urls(webpage_url: str, request_timeout: int, user_agent: str) -> list[str]:
  """
  Fetches a single webpage HTML content and parses image URLs from it.
  """
  if ('www.' in webpage_url):
    raise Exception('fake fetch error')
  return list()


async def retrieve_img_urls(webpage_url_list: list[str], request_timeout: int, user_agent: str) -> dict:
  """
  Concurrently executes all tasks of fetching webpages and parsing image URLs from them.
  Logs errors and only includes successfully parsed webpages into resulting dict:
  `{webpage_url: img_url_list}`.
  """

  task_list = [
    fetch_and_parse_img_urls(url, request_timeout, user_agent)
    for url in webpage_url_list
  ]
  # each element is either an Exception or a list of image URLs
  result_list = await asyncio.gather(*task_list, return_exceptions=True)
  # logging.info(f"Image URLs for all webpages: {result_list}")

  img_urls = dict()
  for i in range(len(webpage_url_list)):
    webpage_url = webpage_url_list[i]
    result = result_list[i]
    if (isinstance(result, Exception)):
      logging.error(f"Failed to fetch or parse {webpage_url}: {result}")
    else:
      img_urls[webpage_url] = result

  return img_urls


async def main(webpage_url_list: list[str], request_timeout: int, user_agent: str) -> None:
  img_urls = await retrieve_img_urls(webpage_url_list, request_timeout, user_agent)
  logging.info(f"Image URLs per webpage: {img_urls}")


if __name__ == '__main__':
  config = read_config('config.ini')
  config_logging(config['log_dirname'], '%Y-%m-%d--%H-%M-%S')

  webpage_list = read_webpage_list(config['input_filename'])
  logging.info(f"List of webpages ({len(webpage_list)}): {webpage_list}")

  asyncio.run(main(webpage_list, config.getint('request_timeout'), config['user_agent']))
