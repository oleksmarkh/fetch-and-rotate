from urllib.parse import urljoin, urldefrag, urlsplit, quote_plus
from bs4 import BeautifulSoup


def convert(url: str) -> tuple[str, str]:
  """
  Converts an absolute URL into a `(dirname, filename)` tuple, e.g.
  ```
  'https://sub.example.org/images/SomeExample.jpg?SomeParam=1' =>
  ('sub.example.org', 'images%2FSomeExample.jpg%3FSomeParam%3D1')
  """

  components = urlsplit(url)
  dirname = components.netloc
  filename = quote_plus(
    components.path[1:]
    if components.query == ''
    else f"{components.path[1:]}?{components.query}"
  )

  return (dirname, filename)


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

  keywords_to_exclude = {'adServer', 'scorecardresearch.com', '1px', 'avatar', 'profile', 'logo', 'static'}
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


def mix(urls: dict[str, list[str]]) -> list[str]:
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

  url_list_list = urls.values()

  if (len(url_list_list) == 0):
    return []

  if (len(url_list_list) == 1):
    return list(url_list_list)[0]

  result = []
  for i in range(0, max(*[len(url_list) for url_list in url_list_list])):
    for url_list in url_list_list:
      if i < len(url_list):
        result.append(url_list[i])

  return result
