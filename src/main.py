import asyncio
import datetime
import logging
import mimetypes
import sys
from configparser import ConfigParser
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath

import requests
from PIL import Image

import fsutils
import urlutils


@dataclass
class Config:
  max_img_count: int
  request_timeout: float
  user_agent: str
  input_filename: str
  log_dirname: str
  download_dirname: str
  output_dirname: str


class ImgStatus(Enum):
  NOT_PROCESSED = 'not-processed'
  DOWNLOADED = 'downloaded'
  PROCESSED = 'processed'


@dataclass
class Img:
  url: str
  dirname: str
  filename: str
  status: ImgStatus = ImgStatus.NOT_PROCESSED


def read_config(filename: str) -> Config:
  config_parser = ConfigParser()
  config_parser.read(filename)
  c = config_parser['DEFAULT']
  return Config(
    c.getint('max_img_count'), c.getfloat('request_timeout'), c['user_agent'],
    c['input_filename'], c['log_dirname'], c['download_dirname'], c['output_dirname']
  )


def config_logging(dirname: str, filename_datetime_format: str) -> None:
  filename = f"{datetime.datetime.now().strftime(filename_datetime_format)}.log"
  fsutils.mkdir(dirname)
  logging.basicConfig(
    format='%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s',
    level=logging.DEBUG,
    handlers=[
      logging.StreamHandler(),
      logging.FileHandler(PurePath(dirname, filename))
    ]
  )


def fetch(url: str, config: Config) -> requests.Response:
  headers = {'User-Agent': config.user_agent}
  response = requests.get(url, timeout=config.request_timeout, headers=headers)
  response.raise_for_status()
  return response


async def fetch_and_parse(webpage_url: str, config) -> list[str]:
  """
  Fetches a single webpage HTML content and parses image URLs from it.
  Resolves each image URL against final webpage URL, accounting for redirects.
  """
  response = fetch(webpage_url, config)
  return urlutils.parse(response.text, response.url)


async def fetch_and_parse_all(webpage_url_list: list[str], config: Config) -> dict[str, list[str]]:
  """
  Concurrently executes all tasks of fetching webpages and parsing image URLs from them.
  Logs errors and only includes successfully parsed webpages into resulting dict:
  `{webpage_url: [img0_url, img1_url, ...]}`.
  """

  task_list = [
    fetch_and_parse(url, config)
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


async def download_and_rotate(img: Img, config: Config) -> Img:
  """
  Downloads, rotates and stores a single image.
  Updates `img.filename` suffix if it can be guessed from its `Content-Type` header.
  Returns image filename.
  """

  response = fetch(img.url, config)
  extension = mimetypes.guess_extension(response.headers['Content-Type'])

  if (extension and not img.filename.endswith(extension)):
    img.filename += extension

  download_dirpath = PurePath(config.download_dirname, img.dirname)
  download_filepath = PurePath(download_dirpath, img.filename)
  output_dirpath = PurePath(config.output_dirname, img.dirname)
  output_filepath = PurePath(output_dirpath, img.filename)

  fsutils.mkdir(download_dirpath)
  fsutils.mkdir(output_dirpath)
  fsutils.write_binary(download_filepath, response.content)

  img.status = ImgStatus.DOWNLOADED

  with Image.open(str(download_filepath)) as img_pillow:
    img_pillow.transpose(Image.ROTATE_180).save(str(output_filepath))
    img.status = ImgStatus.PROCESSED

  return img


async def download_and_rotate_batch(img_list: list[Img], config: Config) -> tuple[int, int]:
  """
  Concurrently executes all tasks of downloading and rotating images.
  Returns a tuple with numbers of failed and successful attempts: `(err_count, success_count)`.
  """

  task_list = [
    download_and_rotate(img, config)
    for img in img_list
  ]
  # each element is either an Exception or an Img object
  result_list = await asyncio.gather(*task_list, return_exceptions=True)

  err_count = 0
  success_count = 0
  for i, result in enumerate(result_list):
    img = img_list[i]
    if (isinstance(result, Exception)):
      err_count += 1
      logging.error(f"Failed to download or rotate {img.url}: {result}")
    else:
      success_count += 1

  return (err_count, success_count)


async def download_and_rotate_all(img_list: list[Img], config: Config) -> tuple[int, int]:
  """
  Slices the first batch of `max_img_count` URLs from `img_list`
  and schedules them for downloading and rotation.
  If some of them fail, slices and runs another batch.
  Repeats until either entire `img_list` is exhausted or a total of `max_img_count` succeed.
  Returns accumulated `(err_count, success_count)` totals for all batches.
  """

  batch_index = 0
  slice_from = 0  # inclusive
  slice_to = config.max_img_count  # exclusive
  err_count_total = 0
  success_count_total = 0
  while True:
    logging.info(f"Downloading and rotating images (batch #{batch_index}): [{slice_from}, {slice_to})")

    err_count, success_count = await download_and_rotate_batch(img_list[slice_from:slice_to], config)
    err_count_total += err_count
    success_count_total += success_count

    logging.info((
      f"Images failed/succeeded/aimed (batch #{batch_index}): "
      f"{err_count}/{success_count}/{slice_to - slice_from}"
    ))

    if (slice_to > len(img_list)):
      logging.warning(f"Image list is exhausted: {len(img_list)}")
      break

    if (success_count_total >= config.max_img_count):
      logging.info(f"Successfully reached {success_count_total} images")
      break

    batch_index += 1
    slice_from = slice_to
    slice_to = slice_from + (config.max_img_count - success_count_total)

  return (err_count_total, success_count_total)


async def main(config: Config) -> None:
  config_logging(config.log_dirname, '%Y-%m-%d--%H-%M-%S')

  webpage_url_list = fsutils.read_line_list(config.input_filename)
  logging.info(f"List of webpages ({len(webpage_url_list)}): {webpage_url_list}")

  img_urls = await fetch_and_parse_all(webpage_url_list, config)
  logging.info(f"Image URLs per webpage: {[(k, len(v)) for k, v in img_urls.items()]}")
  # logging.debug(f"Image URLs per webpage: {img_urls}")

  img_list = [
    Img(
      img_url,
      urlutils.get_dirname(webpage_url),
      urlutils.get_filename(img_url)
    )
    for webpage_url, img_url in urlutils.mix(img_urls)
  ]
  logging.info(f"All image URLs available: {len(img_list)}")
  # logging.debug(f"All image URLs available: {img_list}")

  if (len(img_list) == 0):
    logging.warning("Nothing to download, no image URLs available")
    sys.exit(1)

  err_count, success_count = await download_and_rotate_all(img_list, config)
  logging.info(f"Images failed/succeeded/aimed (total): {err_count}/{success_count}/{config.max_img_count}")
  sys.exit(0 if success_count == config.max_img_count else 1)


if __name__ == '__main__':
  asyncio.run(main(read_config('config.ini')))
