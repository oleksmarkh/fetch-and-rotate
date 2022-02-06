# fetch-and-rotate

## Structure

```bash
├── img-original/
│   └── {website-domain}/
│       └── {image-url-encoded}
├── img-rotated/
│   └── {website-domain}/
│       └── {image-url-encoded}
├── log/
│   └── {YYYY-MM-DD--HH-MM-SS}.log
├── src/
│   ├── tests/
│   ├── fsutils.py
│   ├── main.py
│   └── urlutils.py
├── README.md
├── config.ini  # script config
└── input.txt   # a list of websites (full URLs) to fetch images from
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

# check results
$ tree ./img-rotated/

# lint
$ poetry run pycodestyle --show-source ./src/

# unit tests
$ poetry run pytest ./src/

# cleanup
$ rm ./log/*.log
$ rm -rf ./img-*
```
