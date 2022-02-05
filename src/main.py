import asyncio
import datetime
import logging
import requests
from configparser import ConfigParser, SectionProxy
from pathlib import PurePath
from urllib.parse import urljoin, urldefrag
from bs4 import BeautifulSoup


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


def fetch(url: str, timeout: int, user_agent: str) -> requests.Response:
  headers = {'User-Agent': user_agent}
  return requests.get(url, timeout=timeout, headers=headers)


def normalize_img_url(url: str, base_url: str) -> str:
  return urldefrag(urljoin(base_url, url))[0]


def parse_img_urls(markup: str, base_url: str) -> list[str]:
  """
  Parses image tags from given HTML markup.
  Filters out image URLs containing keywords from hardcoded list.
  Removes fragment (hash) from image URLs.
  Resolves each image URL against given base URL.
  Removes duplicates.
  """

  keywords_to_exclude = {'adServer', 'scorecardresearch.com', '1px', 'avatar', 'profile', 'logo', 'static'}
  soup = BeautifulSoup(markup, 'html.parser')

  # "soup.find_all()" returns a "ResultSet",
  # which may contain different tags with same "src" attr values.
  # Also it's possible to end up with same absolute URLs
  # after resolving different relative URLs and removing fragments.
  # That's why deduplication happens after all transformations.
  return list(set([
    normalize_img_url(img_tag['src'], base_url)
    for img_tag in soup.find_all('img', attrs={'src': True})
    if not any(keyword in img_tag['src'] for keyword in keywords_to_exclude)
  ]))


async def fetch_and_parse_img_urls(
  webpage_url: str, request_timeout: int, user_agent: str
) -> list[str]:
  """
  Fetches a single webpage HTML content and parses image URLs from it.
  Resolves each image URL against final webpage URL, accounting for redirects.
  """

  response = fetch(webpage_url, request_timeout, user_agent)
  return parse_img_urls(response.text, response.url)


async def retrieve_img_urls(
  webpage_url_list: list[str], request_timeout: int, user_agent: str
) -> dict[str, list[str]]:
  """
  Concurrently executes all tasks of fetching webpages and parsing image URLs from them.
  Logs errors and only includes successfully parsed webpages into resulting dict:
  `{webpage_url: [img1_url, img2_url, ...]}`.
  """

  task_list = [
    fetch_and_parse_img_urls(url, request_timeout, user_agent)
    for url in webpage_url_list
  ]
  # each element is either an Exception or a list of image URLs
  result_list = await asyncio.gather(*task_list, return_exceptions=True)

  img_urls = dict()
  for i, webpage_url in enumerate(webpage_url_list):
    result = result_list[i]
    if (isinstance(result, Exception)):
      logging.error(f"Failed to fetch or parse {webpage_url}: {result}")
    else:
      img_urls[webpage_url] = result
      # img_urls[webpage_url] = len(result)

  return img_urls


def mix_urls(urls: dict[str, list[str]]) -> list[str]:
  """
  Flattens a dict (URLs per webpage) into a list of all image URLs,
  by picking URLs from each webpage (iterating over all lists with a common index):
  ```
  {
    p0: [p0[0]],
    p1: [],
    p2: [p2[0], p2[1], p2[2], p2[3]],
    p3: [p3[0], p3[1]],
  } => [
    p0[0], p2[0], p3[0],
           p2[1], p3[1],
           p2[2],
           p2[3]
  ]
  ```
  """

  result = []
  url_list_list = urls.values()
  for i in range(0, max(*[len(url_list) for url_list in url_list_list])):
    for url_list in url_list_list:
      if i < len(url_list):
        result.append(url_list[i])
  return result


async def main(webpage_url_list: list[str], request_timeout: int, user_agent: str) -> None:
  img_urls = await retrieve_img_urls(webpage_url_list, request_timeout, user_agent)
  logging.info(f"Image URLs per webpage ({[(k, len(v)) for k, v in img_urls.items()]}): {img_urls}")

  img_url_list = mix_urls(img_urls)
  logging.info(f"All image URLs available ({len(img_url_list)}): {img_url_list}")


if __name__ == '__main__':
  config = read_config('config.ini')
  config_logging(config['log_dirname'], '%Y-%m-%d--%H-%M-%S')

  webpage_list = read_webpage_list(config['input_filename'])
  logging.info(f"List of webpages ({len(webpage_list)}): {webpage_list}")

  asyncio.run(main(webpage_list, config.getfloat('request_timeout'), config['user_agent']))
