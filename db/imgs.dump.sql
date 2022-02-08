PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE imgs (
  id          INTEGER PRIMARY KEY,
  url         TEXT,
  dirname     TEXT,
  filename    TEXT,
  status      TEXT,
  created_at  NUMERIC DEFAULT CURRENT_TIMESTAMP
);
COMMIT;
