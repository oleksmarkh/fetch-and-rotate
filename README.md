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

* Both `config.ini` and `input.txt` are readable and their content is valid.
* Network is available and webpages are reachable.
* Local FS provides free space and permissions to store the files.
* The goal is to process the first 100 images in no particular order, determined on-the-fly by their availability. The script will NOT try to equally engage with all websites.
* A possibility of same images being accessed under different URLs can be neglected.

## Scenarios

1. Script is executed exactly once. Whatever happens - it aims to fetch/process a given number of images.
2. Script can be executed multiple times, due to various reasons (e.g. the list of webpages changed, significant time passed after previous execution, some webpages are non-idempotent, previous executions failed to process exactly 100 images, etc.).

## Flow

- [ ] Extract config from `config.ini`.
- [ ] Init logging, configure handlers (console and local file).
- [ ] Extract a list of webpages from `input.txt`.
- [ ] Start collecting stats for resulting report.
- [ ] Init a list of image URLs to process.
- [ ] Start fetching all webpages in parallel with `ThreadPoolExecutor` (network-bound).
  - [ ] *Worker thread*: once a webpage is fetched, parse its HTML via `bs4` and report a list of image URLs back to the main thread.
  - [ ] *Main thread*: once each worker's future is completed:
    - [ ] Store number of image URLs retrieved from a given parsed HTML.
    - [ ] Iterate over a list of image URLs received from it:
      - [ ] For each image, decide if it needs to be processed: check if `totals.processed` + `totals.in_processing` (fetching or rotating) is less then 100.
        - [ ] If yes:
          - [ ] *Main thread*: `totals.in_processing += 1`.
          - [ ] *Worker thread*:
            - [ ] `image.status='not-processed'`.
            - [ ] Check if it was already fetched (only when `config.to_force_refetch == false`), i.e. exists on FS at `img-originals/{website-domain}/{image-url-encoded}`.
              - [ ] If yes, rotate and store it directly.
              - [ ] If no, fetch an image, rotate and store it.
              - [ ] Once successfully stored:
                - [ ] `image.status='processed'`.
                - [ ] Report the URL back to the main thread.
                - [ ] Once a successfully processed image URL is received on the *main thread*:
                  - [ ] `totals.in_processing -= 1`.
                  - [ ] `totals.processed += 1`.
- [ ] Log resulting report:
  * Numbers of images (per website and total):
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
* HTML parsing: [`bs4`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* image processing: [`pillow`](https://pillow.readthedocs.io/)
  * [`im.transpose(Image.ROTATE_180)`](https://pillow.readthedocs.io/en/stable/handbook/tutorial.html#transposing-an-image)

## Setup

```bash
$ ...
```
