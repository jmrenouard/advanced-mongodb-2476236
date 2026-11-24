# Tutorial 02: Change Streams, Datasets, and Collections Lab

In this tutorial, you inspect sample JSON datasets (`datasets/`), verify `sharded_cluster/*.conf` configs using Python stdlib, inspect collection scripts, and run a mocked `resumable_change_stream.py` test offline.

## Prerequisites

- Python 3.10+ (`python --version`)
- Repository files present under `datasets/`, `sharded_cluster/`, `change-streams/`, `timeseries/`, `views/`, and `materialized_views/`

## Step 1 — Inspect Dataset Files and Record Counts

Count records across the sample datasets (`books.json`, `filme.json`, `orders.json`, `stocks.json`) cleanly:

```bash
python -B -c "from pathlib import Path; [print(p.name, len(p.read_text(encoding='utf-8').splitlines()), 'lines') for p in sorted(Path('datasets').glob('*.json'))]"
```

Expected output prints the line count for all 4 JSON files cleanly.

## Step 2 — Validate Sharded Cluster Configuration Files

Verify with Python stdlib that every `sharded_cluster/*.conf` binds `localhost`, uses `./keyfile`, and assigns ports `27018–27027`:

```bash
python -B -c "import pathlib, re; [print(p.name, re.findall(r'(?:bindIp|port|keyFile):\s*\S+', p.read_text())) for p in sorted(pathlib.Path('sharded_cluster').glob('*.conf'))]"
```

Expected output shows ports `27018` (`mongos.conf`), `27019–27021` (`cfgsrv1–3.conf`), and `27022–27027` (`m1–6.conf`) all bound to `localhost` with `./keyfile`.

## Step 3 — Inspect MongoDB Shell Collection Scripts

Review the JavaScript examples for time-series, clustered collections, views, and materialized views:

```bash
cat clustered_collections/create_clustered_collection.js
cat timeseries/create_timeseries_collection.js
cat materialized_views/create_view.js
```

## Step 4 — Run Mocked Resumable Change Stream Offline

Verify clean stream termination and `resume_after` cursor recovery in `change-streams/resumable_change_stream.py` using mocked `pymongo` and `bson` modules:

```bash
python -B -c "import importlib.util, json, sys, types; \
  from unittest.mock import MagicMock; \
  Err = type('PyMongoError', (Exception,), {}); \
  sys.modules['pymongo'] = types.SimpleNamespace(errors=types.SimpleNamespace(PyMongoError=Err), MongoClient=MagicMock()); \
  sys.modules['bson'] = types.SimpleNamespace(); \
  sys.modules['bson.json_util'] = types.SimpleNamespace(dumps=json.dumps); \
  spec = importlib.util.spec_from_file_location('rcs', 'change-streams/resumable_change_stream.py'); \
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); \
  client = MagicMock(); client.changestream.collection.watch.return_value.__enter__.return_value = iter([]); \
  m.run_change_stream(client, None, 0); print('WATCH_CALLS', client.changestream.collection.watch.call_count)"
```

Expected output:

```text
WATCH_CALLS 1
```

## Next Steps

- Launch the sandbox sharded cluster using [Launch Sharded Cluster and Import Datasets](../02-how-to-guides/02-launch-sharded-cluster-and-import-datasets.md).
- Look up every port and replica set name in [Sharded Cluster Ports and Configs](../03-reference/02-sharded-cluster-ports-and-configs.md).
- Understand topology and view trade-offs in [Sharded Topology, Views, and Time-Series Design](../04-explanation/02-sharded-topology-views-and-timeseries-design.md).
