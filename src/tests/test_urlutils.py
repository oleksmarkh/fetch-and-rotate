from src.urlutils import get_filename, mix, parse, resolve


def test_get_filename():
  assert get_filename('http://example.org/test.png') == (
    'example.org--test.png'
  )

  assert get_filename('https://sub.example.org/images/SomeExample.jpg?SomeParam=1#hash') == (
    'sub.example.org--images%2FSomeExample--SomeParam%3D1.jpg'
  )


def test_resolve():
  # with trailing slash
  assert resolve('3/4/some.png', 'http://example.org/1/2/') == (
    'http://example.org/1/2/3/4/some.png'
  )

  # without trailing slash
  assert resolve('3/4/some.png', 'http://example.org/1/2') == (
    'http://example.org/1/3/4/some.png'
  )

  # root path
  assert resolve('/1/2/some.png', 'http://example.org/1/2/3/4/') == (
    'http://example.org/1/2/some.png'
  )

  # absolute
  assert resolve('https://example.com/1/2/some.png', 'http://example.org/1/2/3/') == (
    'https://example.com/1/2/some.png'
  )

  # fragment is removed, but query params are kept
  assert resolve('some.png?a=1&b#hash', 'http://example.org/1/2/') == (
    'http://example.org/1/2/some.png?a=1&b'
  )


def test_parse():
  assert parse('<img src="test.jpg">', 'http://example.org') == [
    'http://example.org/test.jpg'
  ]

  assert parse(
    '<img src="first.jpg?size=small#hash-to-be-removed"><br /><img src="/sub/path/second.jpg">',
    'http://example.org/some/'
  ) == [
    'http://example.org/some/first.jpg?size=small',
    'http://example.org/sub/path/second.jpg',
  ]

  assert parse(
    (
      '<section>'
      '  <img src="one.jpg">'
      '  <img src="two.jpg">'
      '  <img src="two.jpg?size=m">'
      '  <img src="three.jpg">'
      '  <img src="two.jpg#again">'
      '  <img src="/some/../two.jpg#yet-again">'
      '</section>'
    ),
    'http://example.org'
  ) == [
    'http://example.org/one.jpg',
    'http://example.org/two.jpg',
    'http://example.org/two.jpg?size=m',
    'http://example.org/three.jpg'
  ]


def test_mix():
  assert mix({}) == []

  assert mix({
    'http://example.org': ['/test.jpg']
  }) == [('http://example.org', '/test.jpg')]

  assert mix({
    'http://some.example.org': ['first.jpg', 'nested/second.png'],
    'http://another.example.com': []
  }) == [('http://some.example.org', 'first.jpg'), ('http://some.example.org', 'nested/second.png')]

  assert mix({
    'http://0.org': ['0-0', '0-1'],
    'http://1.org': ['1-0', '1-1', '1-2', '1-3', '1-4', '1-5'],
    'http://2.org': ['2-0'],
    'http://3.org': [],
    'http://4.org': ['4-0', '4-1', '4-2']
  }) == [
    ('http://0.org', '0-0'), ('http://1.org', '1-0'), ('http://2.org', '2-0'), ('http://4.org', '4-0'),
    ('http://0.org', '0-1'), ('http://1.org', '1-1'),                          ('http://4.org', '4-1'),
                             ('http://1.org', '1-2'),                          ('http://4.org', '4-2'),
                             ('http://1.org', '1-3'),
                             ('http://1.org', '1-4'),
                             ('http://1.org', '1-5')
  ]
