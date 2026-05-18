-- Relational schema for the mobility platform
-- (SQLite-compatible; also works in Postgres with minor tweaks)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  surname TEXT NOT NULL,
  birthdate TEXT NOT NULL,
  country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stations (
  station_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
  trip_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  start_station_id TEXT NOT NULL,
  end_station_id TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  cost REAL NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id),
  FOREIGN KEY(start_station_id) REFERENCES stations(station_id),
  FOREIGN KEY(end_station_id) REFERENCES stations(station_id)
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  trip_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  type TEXT NOT NULL,
  value_json TEXT NOT NULL,
  FOREIGN KEY(trip_id) REFERENCES trips(trip_id)
);

CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_start_station ON trips(start_station_id);
CREATE INDEX IF NOT EXISTS idx_trips_end_station ON trips(end_station_id);
CREATE INDEX IF NOT EXISTS idx_events_trip ON events(trip_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);

