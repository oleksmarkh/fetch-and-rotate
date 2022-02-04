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

* A possibility of same images being accessed under different URLs can be neglected (all images are treated as unique as long as their URLs differ).
* Even though it's not specified in the assignment, the script will try to equally take images from all websites, aiming for robust output.

## Scenarios

1. Script is executed exactly once. Whatever happens - it aims to fetch/process a given number of images.
2. Script can be executed multiple times, due to various reasons (e.g. the list of webpages changed, significant time passed after previous execution, some webpages are non-idempotent, previous executions failed to process exactly 100 images, etc.).

## Flow

- [x] Extract config from `config.ini`.
- [x] Init logging, configure handlers (console and local file).
- [x] Extract a list of webpages from `input.txt`.
<!-- - [ ] Instantiate an `ImageProcessor` (to hold a state of entire process). -->
<!-- - [ ] Start collecting stats for resulting report. -->
- [x] Init a `{webpage: webpage_image_url_list}` dict of all image URLs available for processing.
- [x] Start fetching all webpages in parallel with `asyncio` (network-bound).
  - [ ] *Sub coroutine*:
    - [x] If webpage fetching fails: return an error.
    - [ ] If fetching succeeds, parse its HTML content with `bs4`:
      - [ ] If parsing fails: return an error.
      - [ ] If parsing succeeds: report a list of image URLs back to the main coroutine (even if it's empty).
  - [ ] *Main coroutine*:
    - [x] Once each worker's reports back, update the dict:
      - [x] If worker fails to fetch or parse: log an error.
      - [x] If worker succeeds: insert a list of image URLs.
    - [ ] Once all workers are finished:
      - [ ] Convert the dict into a list of all image URLs, by picking URLs from each webpage (until there are no more URLs to pick): `[p0[0], p1[0], p2[0], p0[1], p2[1], p0[2], p2[2], ...]`
        - [ ] Cover this function with unit tests.
      - [ ] Slice first 100 image URLs from this "normalized" list and start fetching the images in parallel (network-bound).
        - [ ] *Sub coroutine*:
          - [ ] `image.status='not-processed'`.
          - [ ] Check if it was already fetched (only when `config.to_force_refetch == false`), i.e. exists on FS at `img-originals/{website-domain}/{image-url-encoded}`.
            - [ ] If yes, rotate and store it directly.
            - [ ] If no, fetch an image, rotate and store it.
              - [ ] If any of the steps fail:
                - [ ] `image.status='failed_to_...'`.
                - [ ] Log an error and report it back.
            - [ ] Once successfully stored:
              - [ ] `image.status='processed'`.
              - [ ] Report the URL back to the main coroutine.
        - [ ] *Main coroutine*:
          - [ ] If an error is received from any worker, spawn another one for processing the next image from the list (101-st, 102-nd, ...).
          - [ ] Once 100 images were successfully processed or the list is exhausted (no more URLs to try), log the resulting report:
            * Numbers of images (per webpage and total):
              * Available for fetching.
              * Fetched.
              * Failed/succeeded to rotate.
            * If there were less then 100 total images successfully processed, suggest to update `input.txt` entries for the next run.

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
