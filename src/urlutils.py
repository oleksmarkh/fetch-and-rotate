from pathlib import PurePath
from urllib.parse import urljoin, urldefrag, urlsplit, quote_plus
from bs4 import BeautifulSoup


def recompose(hostname: str, path: str, query: str, delimiter: str) -> str:
  if query == '':
    return delimiter.join([hostname, path])

  p = PurePath(path)
  return delimiter.join([
    hostname,
    str(p.with_stem(delimiter.join([p.stem, query])).with_suffix(''.join(p.suffixes)))
  ])


def get_dirname(url: str) -> str:
  return urlsplit(url).hostname


def get_filename(url: str) -> str:
  """
  Converts an absolute image URL into a its filename representation by:
  * using hostname as prefix
  * removing the leading slash from the path
  * moving the query part before path suffix

  For example:
  ```
  'https://sub.example.org/images/SomeExample.jpg?SomeParam=1' =>
  'sub.example.org--images%2FSomeExample--SomeParam%3D1.jpg'
  ```
  """
  components = urlsplit(url)
  return quote_plus(recompose(components.hostname, components.path[1:], components.query, '--'))


def resolve(url: str, base_url: str) -> str:
  """
  Returns an absolute URL without a fragment.
  """
  return urldefrag(urljoin(base_url, url))[0]


def parse(markup: str, base_url: str) -> list[str]:
  """
  Parses image tags from given HTML markup.
  Filters out image URLs containing keywords from hardcoded list.
  Resolves each image URL against given base URL.
  Removes fragment (hash) from image URLs, since those aren't sent over HTTP.
  Removes duplicates.
  """

  keywords_to_exclude = {'adServer', 'scorecardresearch.com', '1px', 'avatar', 'profile', 'logo', 'static', '.svg'}
  soup = BeautifulSoup(markup, 'html.parser')

  # "soup.find_all()" returns a "ResultSet",
  # which may contain different tags with same "src" attr values.
  # Also it's possible to end up with same absolute URLs
  # after resolving different relative URLs and removing fragments.
  # That's why deduplication happens after all transformations.
  return list(set([
    resolve(img_tag['src'], base_url)
    for img_tag in soup.find_all('img', attrs={'src': True})
    if not any(keyword in img_tag['src'] for keyword in keywords_to_exclude)
  ]))


def mix(urls: dict[str, list[str]]) -> list[tuple[str, str]]:
  """
  Flattens a dict (URLs per webpage) into a list of `(webpage_url, img_url)` tuples,
  by picking URLs from each webpage (iterating over all lists with a common index):
  ```
  {
    p0: [p0[0]],
    p1: [],
    p2: [p2[0], p2[1], p2[2], p2[3]],
    p3: [p3[0], p3[1]],
  } => [
    (p0, p0[0]), (p2, p2[0]), (p3, p3[0]),
                 (p2, p2[1]), (p3, p3[1]),
                 (p2, p2[2]),
                 (p2, p2[3])
  ]
  ```
  """

  webpage_url_list = list(urls.keys())
  url_list_list = urls.values()

  if (len(url_list_list) == 0):
    return []

  if (len(url_list_list) == 1):
    return [
      (webpage_url_list[0], url)
      for url in list(url_list_list)[0]
    ]

  result = []
  for i in range(0, max(*[len(url_list) for url_list in url_list_list])):
    for j, url_list in enumerate(url_list_list):
      if i < len(url_list):
        result.append((webpage_url_list[j], url_list[i]))

  return result
