import asyncio
import datetime
import logging
from urllib import response
import requests
import sys
from configparser import ConfigParser, SectionProxy
from pathlib import PurePath

import urlutils


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
  response = requests.get(url, timeout=timeout, headers=headers)
  response.raise_for_status()
  return response


async def fetch_and_parse(
  webpage_url: str, request_timeout: int, user_agent: str
) -> list[str]:
  """
  Fetches a single webpage HTML content and parses image URLs from it.
  Resolves each image URL against final webpage URL, accounting for redirects.
  """
  response = fetch(webpage_url, request_timeout, user_agent)
  return urlutils.parse(response.text, response.url)


async def fetch_and_parse_all(
  webpage_url_list: list[str], request_timeout: int, user_agent: str
) -> dict[str, list[str]]:
  """
  Concurrently executes all tasks of fetching webpages and parsing image URLs from them.
  Logs errors and only includes successfully parsed webpages into resulting dict:
  `{webpage_url: [img0_url, img1_url, ...]}`.
  """

  task_list = [
    fetch_and_parse(url, request_timeout, user_agent)
    for url in webpage_url_list
  ]
  # each element is either an Exception or a list of image URLs
  result_list = await asyncio.gather(*task_list, return_exceptions=True)

  img_urls = dict()
  for i, result in enumerate(result_list):
    webpage_url = webpage_url_list[i]
    if (isinstance(result, Exception)):
      logging.error(f"Failed to fetch or parse {webpage_url}: {result}")
    else:
      img_urls[webpage_url] = result

  return img_urls


async def download_and_rotate(
  img_url: str, request_timeout: int, user_agent: str,
  originals_dirname: str, output_dirname: str
) -> str:
  """
  Downloads, rotates and stores a single image.
  Returns image filename.
  """
  response = fetch(img_url, request_timeout, user_agent)
  img_filename = urlutils.convert(img_url)
  # TODO: pass a webpage domain as "webpage_dirname"
  with open(PurePath(originals_dirname, webpage_dirname, img_filename), 'wb') as img_file:
    img_file.write(response.content)
  return img_filename


async def download_and_rotate_batch(
  img_url_list: list[str], request_timeout: int, user_agent: str,
  originals_dirname: str, output_dirname: str
) -> tuple[int, int]:
  """
  Concurrently executes all tasks of downloading and rotating images.
  Returns a tuple with numbers of failed and successful attempts: `(err_count, success_count)`.
  """

  task_list = [
    download_and_rotate(
      url, request_timeout, user_agent,
      originals_dirname, output_dirname
    )
    for url in img_url_list
  ]
  # each element is either an Exception or an image filename
  result_list = await asyncio.gather(*task_list, return_exceptions=True)

  err_count = 0
  success_count = 0
  for i, result in enumerate(result_list):
    img_url = img_url_list[i]
    if (isinstance(result, Exception)):
      err_count += 1
      logging.error(f"Failed to download or rotate {img_url}: {result}")
    else:
      success_count += 1
      # logging.info(f"Successfully downloaded and rotated: {img_url}")

  return (err_count, success_count)


async def download_and_rotate_all(
  img_url_list: list[str], max_img_count: int,
  request_timeout: int, user_agent: str,
  originals_dirname: str, output_dirname: str
) -> tuple[int, int]:
  """
  Slices the first batch of `max_img_count` URLs from `img_url_list`
  and schedules them for downloading and rotation.
  If some of them fail, slices and runs another batch.
  Repeats until either entire `img_url_list` is exhausted or a total of `max_img_count` succeed.
  Returns accumulated `(err_count, success_count)` totals for all batches.
  """

  batch_index = 0
  slice_from = 0  # inclusive
  slice_to = max_img_count  # exclusive
  err_count_total = 0
  success_count_total = 0
  while True:
    logging.info(f"Downloading and rotating images (batch #{batch_index}): [{slice_from}, {slice_to})")
    err_count, success_count = await download_and_rotate_batch(
      img_url_list[slice_from:slice_to],
      request_timeout, user_agent,
      originals_dirname, output_dirname
    )
    err_count_total += err_count
    success_count_total += success_count
    logging.info((
      f"Images failed/succeeded/aimed (batch #{batch_index}): "
      f"{err_count}/{success_count}/{slice_to - slice_from}"
    ))

    if (slice_to > len(img_url_list)):
      logging.warning(f"Image URL list is exhausted: {len(img_url_list)}")
      break

    if (success_count_total >= max_img_count):
      logging.info(f"Successfully reached {success_count_total} images")
      break

    batch_index += 1
    slice_from = slice_to
    slice_to = slice_from + (max_img_count - success_count_total)

  return (err_count_total, success_count_total)


async def main(
  webpage_url_list: list[str], max_img_count: int,
  request_timeout: int, user_agent: str,
  originals_dirname: str, output_dirname: str
) -> None:
  img_urls = await fetch_and_parse_all(webpage_url_list, request_timeout, user_agent)
  logging.info(f"Image URLs per webpage: {[(k, len(v)) for k, v in img_urls.items()]}")
  # logging.debug(f"Image URLs per webpage: {img_urls}")

  img_url_list = urlutils.mix(img_urls)
  logging.info(f"All image URLs available: {len(img_url_list)}")
  # logging.debug(f"All image URLs available: {img_url_list}")

  if (len(img_url_list) == 0):
    logging.warning("Nothing to download, no image URLs available")
    sys.exit(1)

  err_count, success_count = await download_and_rotate_all(
    img_url_list, max_img_count,
    request_timeout, user_agent,
    originals_dirname, output_dirname
  )
  logging.info(f"Images failed/succeeded/aimed (total): {err_count}/{success_count}/{max_img_count}")
  sys.exit(0 if success_count == max_img_count else 1)


if __name__ == '__main__':
  config = read_config('config.ini')
  config_logging(config['log_dirname'], '%Y-%m-%d--%H-%M-%S')

  webpage_list = read_webpage_list(config['input_filename'])
  logging.info(f"List of webpages ({len(webpage_list)}): {webpage_list}")

  asyncio.run(main(
    webpage_list,
    config.getint('max_img_count'), config.getfloat('request_timeout'),
    config['user_agent'], config['originals_dirname'], config['output_dirname']
  ))
