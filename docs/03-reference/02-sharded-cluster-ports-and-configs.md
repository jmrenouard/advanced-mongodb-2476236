# Sharded Cluster Ports and Configurations

## Node Topology Matrix

Every configuration under `sharded_cluster/*.conf` binds `net.bindIp: localhost`, enables `security.keyFile: ./keyfile`, logs to `./data/...`, and sets `processManagement.fork: true`:

| Config File | Cluster Role | Replica Set / Router | TCP Port | `storage.dbPath` / `configDB` |
| :--- | :--- | :--- | ---: | :--- |
| `sharded_cluster/mongos.conf` | `mongos` router | Router | `27018` | `configReplSet/localhost:27019,localhost:27020,localhost:27021` |
| `sharded_cluster/cfgsrv1.conf` | `configsvr` | `configReplSet` | `27019` | `./data/cfg/c1` |
| `sharded_cluster/cfgsrv2.conf` | `configsvr` | `configReplSet` | `27020` | `./data/cfg/c2` |
| `sharded_cluster/cfgsrv3.conf` | `configsvr` | `configReplSet` | `27021` | `./data/cfg/c3` |
| `sharded_cluster/m1.conf` | `shardsvr` | `shard1` | `27022` | `./data/shard1/m1` |
| `sharded_cluster/m2.conf` | `shardsvr` | `shard1` | `27023` | `./data/shard1/m2` |
| `sharded_cluster/m3.conf` | `shardsvr` | `shard1` | `27024` | `./data/shard1/m3` |
| `sharded_cluster/m4.conf` | `shardsvr` | `shard2` | `27025` | `./data/shard2/m4` |
| `sharded_cluster/m5.conf` | `shardsvr` | `shard2` | `27026` | `./data/shard2/m5` |
| `sharded_cluster/m6.conf` | `shardsvr` | `shard2` | `27027` | `./data/shard2/m6` |

## Setup Scripts Order

| Script | Target / Action | Notes |
| :--- | :--- | :--- |
| `sharded_cluster/script` | Creates `data/` folders and launches 9 `mongod` daemons | Run inside `sharded_cluster/` after `chmod 0400 keyfile` |
| `sharded_cluster/script2` | `rs.initiate()`, creates `admin` (`passwordPrompt()`), adds `:27020`, `:27021` | Execute against `localhost:27019` |
| `sharded_cluster/script3` | `rs.initiate()`, creates `admin`, adds `:27023`, `:27024` | Execute against `localhost:27022` |
| `sharded_cluster/script4` | `rs.initiate()`, creates `admin`, adds `:27026`, `:27027` | Execute against `localhost:27025` |
| `sharded_cluster/script5` | Launches `mongos -f mongos.conf` and connects `mongosh --port 27018` | Connects router on `:27018` |
| `sharded_cluster/script6` | Authenticates `admin` and executes `sh.addShard(...)` for `shard1` & `shard2` | Followed by `exercises/script` (`sh.shardCollection("test.filme", {genre: 1})`) |
