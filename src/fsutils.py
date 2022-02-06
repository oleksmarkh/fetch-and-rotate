from pathlib import Path


def read_line_list(filepath: str) -> list[str]:
  with open(filepath) as file:
    return file.read().splitlines()


def write_binary(filepath: str, content: bytes) -> None:
  with open(filepath, 'wb') as file:
    file.write(content)


def mkdir(dirpath: str) -> None:
  Path(dirpath).mkdir(parents=True, exist_ok=True)
