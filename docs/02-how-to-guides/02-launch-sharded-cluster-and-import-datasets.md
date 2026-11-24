# Launch Sharded Cluster and Import Datasets

This guide tells how to start the 9-node local sharded cluster and import sample JSON datasets.

**Prerequisites:**

- You must have `mongod`, `mongos`, `mongosh`, and `mongoimport` installed in `PATH`.
- You must confirm TCP ports `27018` through `27027` are free on `localhost`.

WARNING: NEVER USE THE REPOSITORY DEMO `sharded_cluster/keyfile` IN PRODUCTION. SHARED PUBLIC KEYFILES ALLOW UNAUTHORIZED REPLICA SET AUTHENTICATION.

CAUTION: KEEP ALL CLUSTER INTERFACES BOUND TO `localhost` DURING LABS. EXPOSED UNPROTECTED NODES CAN ALLOW REMOTE WRITE ACCESS.

## Procedure

1. Open the `sharded_cluster` directory and restrict `keyfile` permissions (`0400`).

   ```bash
   cd sharded_cluster && chmod 0400 keyfile
   ```

2. Create data folders and start all config servers and shard nodes (`27019` to `27027`).

   ```bash
   bash ./script
   ```

3. Connect to `localhost:27019` and execute `script2` in `mongosh` to start `configReplSet`.

4. Connect to `localhost:27022` and `localhost:27025`, then run `script3` and `script4`.

5. Start the `mongos` router on port `27018` (`script5`) and add both shards (`script6`).

6. Open `datasets/` and import the four JSON files with `mongoimport`.

   ```bash
   cd ../datasets && bash ./script
   ```

NOTE: The `datasets/script` tool prompts interactively for the `admin` user password configured during replica set setup.

## Verification

1. Connect to `mongos` on port `27018` and inspect shard health.

   ```bash
   mongosh --port 27018 -u admin --authenticationDatabase admin --eval "sh.status()"
   ```

2. Confirm imported collections exist inside the `test` database.

   ```bash
   mongosh --port 27018 -u admin --authenticationDatabase admin --eval "db.getSiblingDB('test').getCollectionNames()"
   ```

## Rollback

Stop all lab `mongos` and `mongod` processes and remove `sharded_cluster/data/`:

```bash
pkill -f "sharded_cluster/" || true
rm -rf sharded_cluster/data
```

## References

- Node port and file matrix: [Sharded Cluster Ports and Configs](../03-reference/02-sharded-cluster-ports-and-configs.md)
- Topology design overview: [Sharded Topology, Views, and Time-Series Design](../04-explanation/02-sharded-topology-views-and-timeseries-design.md)
