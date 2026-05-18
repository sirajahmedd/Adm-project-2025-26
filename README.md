# 🚲 City Mobility Platform — Advanced Data Management Project

> **Course:** Advanced Data Management (A.Y. 2025/2026)  
> **Institution:** Politecnico di Milano  
> **Topic:** Multi-paradigm database management for a shared electric vehicle rental system across Italian cities

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Data Model](#-data-model)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Setup & Installation](#-setup--installation)
- [Part 1 — Relational vs. Document Model](#-part-1--relational-vs-document-model)
- [Part 2 — Graph Model](#-part-2--graph-model)
- [Part 3 — Partitioning & Replication](#-part-3--partitioning--replication)
- [Benchmarking & Scalability](#-benchmarking--scalability)
- [Dataset](#-dataset)

---

## 🗺 Project Overview

The **City Mobility Platform** is the data management backend of a short-term shared electric vehicle rental system operating across multiple Italian cities. The project implements and compares three distinct database paradigms — **Relational**, **Document-oriented**, and **Graph** — to manage the platform's core data, evaluate query performance at scale, and reason about schema evolution, partitioning, and replication strategies.

The system tracks:

| Entity | Description |
|--------|-------------|
| **Users** | Registered riders with personal info |
| **Stations** | Pick-up/drop-off points across cities |
| **Trips** | Individual rental journeys |
| **Events** | Real-time telemetry generated during trips (GPS, ERROR, BATTERY, DELAY) |

---

## 🏗 System Architecture

```
City Mobility Platform
│
├── Relational DB (SQLite / PostgreSQL)
│     └── Normalized tables: users, stations, trips, events
│
├── Document DB (MongoDB)
│     └── Embedded trip documents with nested user, station, and event data
│
├── Graph DB (Neo4j)
│     └── Nodes: USER, TRIP, STATION
│     └── Edges: PERFORMED, STARTS_AT, ENDS_AT
│
└── Spark (PySpark + GraphFrames)
      └── Distributed query execution over MongoDB collections and graph data
```

---

## 🗂 Data Model

### Relational Schema (SQLite / PostgreSQL)

```
users(user_id PK, name, surname, birthdate, country)

stations(station_id PK, name, city, capacity)

trips(trip_id PK, user_id FK→users, start_station_id FK→stations,
      end_station_id FK→stations, start_time, end_time, cost)

events(event_id PK, trip_id FK→trips, timestamp, type, value_json)
```

The relational model uses full **normalization** with foreign-key references, keeping each entity in its own table. This avoids duplication and supports efficient aggregations across entities.

### Document Schema (MongoDB)

Each trip document **embeds** the full user, start station, end station, and all associated events directly:

```json
{
  "_id": "t_000001",
  "trip_id": "t_000001",
  "user": { "user_id": "u_000271", "name": "Linda", "surname": "Diaz", "birthdate": "1995-02-15", "country": "American Samoa" },
  "start_station": { "station_id": "s_000030", "name": "Station 30", "city": "Catania", "capacity": 60 },
  "end_station":   { "station_id": "s_000028", "name": "Station 28", "city": "Milan",   "capacity": 40 },
  "start_time": "2026-02-13T04:12:11Z",
  "end_time":   "2026-02-13T04:51:11Z",
  "cost": 9.51,
  "events": [
    { "timestamp": "2026-02-13T04:25:11Z", "type": "BATTERY", "value": { "pct": 26 } },
    { "timestamp": "2026-02-13T04:38:11Z", "type": "BATTERY", "value": { "pct": 64 } }
  ]
}
```

The embedding strategy enables single-document reads for all trip-related queries.

### Graph Schema (Neo4j)

```
(:USER)   -[:PERFORMED]->  (:TRIP)
(:TRIP)   -[:STARTS_AT]->  (:STATION)
(:TRIP)   -[:ENDS_AT]->    (:STATION)
```

Constraints enforce uniqueness on `user_id`, `trip_id`, and `station_id` (see `cypher/constraints.cypher`).

---

## 📁 Project Structure

```
City-Mobility-Platform/
│
├── cypher/
│   └── constraints.cypher          # Neo4j uniqueness constraints
│
├── data/                           # Base dataset (1k users, 10k trips, 2 events/trip)
│   ├── mobility.sqlite             # SQLite relational database
│   ├── users.jsonl                 # Users — for MongoDB import
│   ├── stations.jsonl              # Stations — for MongoDB import
│   ├── trips.jsonl                 # Trips (flat, references only) — for MongoDB import
│   ├── trip_docs.jsonl             # Trip documents (fully embedded) — for MongoDB import
│   └── events.jsonl                # Events (flat) — for MongoDB import
│
└── data_bench/                     # Benchmark datasets at varying scales
    ├── u1000_t10000_e0/            # 1k users, 10k trips, 0 events/trip
    ├── u1000_t10000_e2/            # 1k users, 10k trips, 2 events/trip
    ├── u1000_t10000_e5/            # 1k users, 10k trips, 5 events/trip
    └── u10000_t10000_e0/           # 10k users, 10k trips, 0 events/trip
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Relational DB | SQLite (prototype) / PostgreSQL (production) |
| Document DB | MongoDB |
| Graph DB | Neo4j |
| Programming Language | Python 3 |
| Relational Driver | `pg8000` (PostgreSQL) or built-in `sqlite3` |
| Document Driver | `PyMongo` |
| Graph Driver | `neo4j` Python driver |
| Distributed Computing | Apache Spark / PySpark |
| Graph Analytics | GraphFrames |
| Data Manipulation | Pandas, NumPy, SciPy |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.8+
- Java JDK 8 (required for PySpark)
- MongoDB running locally or via Atlas
- Neo4j running locally or via Aura

### Install Python Dependencies

```bash
pip install pymongo neo4j pg8000 pyspark pandas numpy scipy
```

> **GraphFrames:** Follow the [official quickstart](https://graphframes.io/02-quick-start/02-quick-start.html) to install alongside PySpark.

### Load the Relational Database (SQLite)

The SQLite database is ready to use — no setup required:

```bash
# Example: open with Python
python3 -c "import sqlite3; conn = sqlite3.connect('data/mobility.sqlite'); print('Connected')"
```

### Load Data into MongoDB

```bash
mongoimport --db mobility --collection users    --file data/users.jsonl
mongoimport --db mobility --collection stations --file data/stations.jsonl
mongoimport --db mobility --collection trips    --file data/trips.jsonl
mongoimport --db mobility --collection trip_docs --file data/trip_docs.jsonl
mongoimport --db mobility --collection events   --file data/events.jsonl
```

### Load Data into Neo4j

1. Apply constraints first:
   ```cypher
   -- Run contents of cypher/constraints.cypher in Neo4j Browser or cypher-shell
   ```

2. Load nodes and relationships using the Neo4j Python driver and the JSONL files (users, stations, trips).

---

## 📊 Part 1 — Relational vs. Document Model

### Implemented Queries

| # | Query |
|---|-------|
| Q1 | Return all trips with user info, start and end station names |
| Q2 | Return all users with number of trips and average trip duration |
| Q3 | Return all stations with number of trips starting and ending there |
| Q4 | Return all trips containing at least one `ERROR` event |

Both the relational (SQLite/PostgreSQL) and document-based (MongoDB) implementations are provided, with performance compared across all benchmark dataset configurations.

### Schema Evolution — BATTERY Events

A key design analysis concerns how to add a `battery_level` integer field (0–100) to all `BATTERY`-type events:

- **Relational:** Requires an `ALTER TABLE events ADD COLUMN battery_level INTEGER` migration. All existing rows receive `NULL` unless backfilled. Schema is enforced uniformly.
- **Document:** No migration needed — new `BATTERY` events simply include the new field. Older documents remain valid without modification, demonstrating the natural **schema flexibility** of the document model.

### Spark-based Implementation (Query 2)

A PySpark implementation of Query 2 (users → trip count + avg duration) is provided over the MongoDB document collection, comparing performance with the native in-database execution at all scale levels.

---

## 🔗 Part 2 — Graph Model

### Graph Queries

| # | Query |
|---|-------|
| GQ1 | Given a user, find all stations reachable through their trips |
| GQ2 | Find the 3 most important stations by total number of incoming + outgoing trips |

Implemented in Cypher (Neo4j) with performance evaluated across benchmark configurations.

### Spark / GraphFrames Queries

| # | Query |
|---|-------|
| SQ1 | Top-3 most important stations by **PageRank** (using GraphFrames) |
| SQ2 | **Connected components** of the station sub-graph (using GraphFrames) |

PageRank and connected components are computed via the [GraphFrames library](https://graphframes.io/).

---

## 🗄 Part 3 — Partitioning & Replication

### Partitioning Strategy

The trip collection is analyzed under two partitioning schemes:

- **Partition by `user_id`:** Benefits user-centric queries (Q2, GQ1). Can cause scatter across shards for station-centric queries (Q3, GQ2).
- **Partition by `start_station_id`:** Benefits station-centric queries (Q3, GQ2). Leads to fan-out for user-centric queries.

The report discusses the trade-offs and recommends a strategy based on the query workload profile.

### Replication Strategy

The system assumes a **single-leader, asynchronous replication** setup with 1 primary and 2 secondary replicas. The analysis covers:

- Which queries are safe to serve from a secondary (read-only, tolerate stale data).
- Which queries require primary access to guarantee consistency (e.g., post-trip write immediately followed by aggregation reads).
- Potential inconsistency scenarios and mitigation strategies.

---

## 📈 Benchmarking & Scalability

Queries are evaluated across the following parameter combinations:

| Parameter | Values |
|-----------|--------|
| Number of users | 1,000 / 10,000 / 50,000 |
| Number of trips | 10,000 / 50,000 / 100,000 |
| Events per trip | 0 / 2 / 5 / 10 |

Pre-generated benchmark datasets are provided in `data_bench/` for a subset of these configurations. Larger datasets can be generated with the included data generation script.

---

## 📦 Dataset

All data files use **JSONL format** (one JSON object per line) for portability. The base dataset contains:

| Collection | Count |
|-----------|-------|
| Users | 1,000 |
| Stations | 200 (across multiple Italian cities) |
| Trips | 10,000 |
| Events | ~20,000 (avg. 2 per trip) |

Data is synthetically generated with realistic timestamps, cost values, and event distributions.

---

## 📄 License

This project was developed as an academic assignment for the Advanced Data Management course at Politecnico di Milano (A.Y. 2025/2026). All data is synthetically generated and is intended for educational use only.
