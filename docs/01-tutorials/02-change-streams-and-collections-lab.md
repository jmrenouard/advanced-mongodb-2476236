# Tutorial 02: Change Streams, Datasets, and Collections Lab

In this tutorial, you inspect sample JSON datasets (`datasets/`), verify `sharded_cluster/*.conf` YAML configs, and run a mocked `resumable_change_stream.py` test offline.

## Prerequisites

- Python 3.10+ (`python --version`)
- Repository files present under `datasets/`, `sharded_cluster/`, `timeseries/`, `views/`, and `materialized_views/`

## Step 1 — Inspect Dataset Files and Record Counts

Count records across the sample datasets (`books.json`, `filme.json`, `orders.json`, `stocks.json`) cleanly:

```bash
python -B -c "from pathlib import Path; [print(p.name, len(p.read_text(encoding='utf-8').splitlines()), 'lines') for p in sorted(Path('datasets').glob('*.json'))]"
```

Expected output prints the line count for all 4 JSON files cleanly.

## Step 2 — Validate Sharded Cluster Configuration Files

Verify that every configuration file in `sharded_cluster/*.conf` binds `localhost` only and declares valid YAML syntax:

```bash
python -B -c "import yaml, pathlib; [print(p.name, yaml.safe_load(p.read_text())['net']) for p in sorted(pathlib.Path('sharded_cluster').glob('*.conf'))]"
```

Expected output shows ports `27018` (`mongos.conf`), `27019–27021` (`cfgsrv1–3.conf`), and `27022–27027` (`m1–6.conf`) all bound to `localhost`.

## Step 3 — Inspect MongoDB Shell Collection Scripts

Review the JavaScript examples for time-series, clustered collections, views, and materialized views:

```bash
cat clustered_collections/create_clustered_collection.js
cat timeseries/create_timeseries_collection.js
cat materialized_views/create_view.js
```

## Next Steps

- Launch the sandbox sharded cluster using [Launch Sharded Cluster and Import Datasets](../02-how-to-guides/02-launch-sharded-cluster-and-import-datasets.md).
- Look up every port and replica set name in [Sharded Cluster Ports and Configs](../03-reference/02-sharded-cluster-ports-and-configs.md).
- Understand topology and view trade-offs in [Sharded Topology, Views, and Time-Series Design](../04-explanation/02-sharded-topology-views-and-timeseries-design.md).
