# fetch-and-rotate

## Structure

```bash
├── img-originals/
│   └── {website-domain}/
│       └── {image-url-encoded}
├── img-rotated/
│   └── {website-domain}/
│       └── {image-url-encoded}
├── log/
│   └── {YYYY-MM-DD--HH-MM-SS}.log
├── src/
│   ├── tests/
│   └── main.py
├── README.md
├── assignment.md
├── config.ini     # script config
└── input.txt      # a list of websites (full URLs) to fetch images from
```

## Assumptions

### Execution env

* Both `config.ini` and `input.txt` are readable and their content is valid.
* Network is available, but it's not given that all webpages are reachable.
* There's enough RAM to handle all the images.
* Local FS provides permissions and enough free space to store the files.

### Functional

* A possibility of same images being accessed under different URLs can be
neglected (all images are treated as unique as long as their URLs differ).
* Even though it's not specified in the assignment,
the script will try to equally take images from all websites,
aiming for robust output.

## Scenarios

1. Script is executed exactly once.
Whatever happens - it aims to fetch/process a given number of images.
2. Script can be executed multiple times, due to various reasons, e.g.:
* Previous executions failed to process exactly 100 images.
* The list of webpages changed.
* Some webpages are non-idempotent (content changed).

## Possible improvements.

Manage a `set()` to `asyncio.wait()` for `asyncio.create_task()`
to schedule image processing in a pool (concurrent queue),
instead of batching until success or exhaustion.
Additionally, it would limit the number of outbound connections.

## Flow

- [x] Extract config from `config.ini`.
- [x] Init logging, configure handlers (console and local file).
- [x] Extract a list of webpages from `input.txt`.
- [x] Start fetching all webpages in parallel with `asyncio` (network-bound).
- [x] *Sub coroutine*:
  - [x] If webpage fetching fails: return an error.
  - [x] If fetching succeeds, parse its HTML content with `bs4`:
    - [x] If parsing fails: return an error.
    - [x] If parsing succeeds:
      - [x] Remove fragment (hash) from image URLs.
      - [x] Filter out image URLs based on hardcoded list of keywords.
      - [x] Resolve all image URLs against webpage final URL, accounting for redirects.
      - [x] Deduplicate the list of image URLs.
      - [x] Return a list of image URLs back to the main coroutine (even if it's empty).
- [ ] *Main coroutine*: once all sub coroutines are finished:
  - [x] If any sub coroutine fails to fetch or parse: log an error.
  - [x] Compose a `{webpage_url: [img1_url, img2_url, ...]}` dict of all image URLs available for processing.
  - [x] Mix all image URLs by picking them from each webpage (common-index iteration).
    - [ ] Cover this function with unit tests.
  - [x] Slice the first batch of 100 image URLs from this "mixed" list and start fetching the images in parallel (network-bound).
  - [ ] *Sub coroutine*:
    - [ ] `image.status='not-processed'`.
    - [ ] Check if it was already fetched (only when `config.to_force_refetch == false`), i.e. exists on FS at `img-originals/{website-domain}/{image-url-encoded}`.
      - [ ] If yes, rotate and store it directly.
      - [ ] If no, fetch an image, rotate and store it.
        - [ ] If any of the steps fail:
          - [ ] `image.status='failed_to_...'`.
          - [ ] Return an error.
      - [ ] Once successfully stored:
        - [ ] `image.status='processed'`.
        - [x] Return the URL back to the main coroutine.
  - [x] *Main coroutine*:
    - [x] If errors were received from sub coroutines, slice and run another batch.
    - [x] Once 100 images were successfully processed or the list is exhausted (no more URLs to try).
    - [x] Exit with error/success status.

## Dev dependencies

* python versioning: [`pyenv`](https://github.com/pyenv/pyenv/)
* env/deps management: [`poetry`](https://python-poetry.org/docs/basic-usage/)
* linter: [`pycodestyle`](https://pycodestyle.readthedocs.io/en/latest/)
* unit tests: [`pytest`](https://pytest.org/en/latest/)

## Dependencies

* HTTP transport: [`requests`](https://docs.python-requests.org/en/latest/user/quickstart/)
* HTML parsing: [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* image processing: [`pillow`](https://pillow.readthedocs.io/)
  * [`im.transpose(Image.ROTATE_180)`](https://pillow.readthedocs.io/en/stable/handbook/tutorial.html#transposing-an-image)

## Commands

```bash
# python version
$ brew install pyenv
$ pyenv install 3.10.2

# deps
$ curl -sSL https://install.python-poetry.org | python3 -
$ poetry install

# run
$ time poetry run python ./src/main.py

# lint
$ poetry run pycodestyle --show-source ./src/

# unit tests
$ poetry run pytest ./src/

# clean logs
$ rm ./log/*.log
```
