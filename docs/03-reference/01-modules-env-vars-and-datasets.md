# Modules, Environment Variables, and Datasets

## Python Modules and Environment Variables

| Script | Env Var | Dependencies (`requirements.txt`) | Database / Collection Target |
| :--- | :--- | :--- | :--- |
| `change-streams/main.py` | `CHANGE_STREAM_DB` | `pymongo` | `changestream.collection` (`insert_one`, `update_one`, `delete_one`) |
| `change-streams/change_stream.py` | `CHANGE_STREAM_DB` | `pymongo` | `changestream.collection.watch()` |
| `change-streams/change_stream_2.py` | `CHANGE_STREAM_DB` | `pymongo` | Filtered `watch()` on `operationType: update` and `address` |
| `change-streams/resumable_change_stream.py` | `CHANGE_STREAM_DB` | `pymongo` | Resumable `watch(resume_after=resume_token)` with iterative exponential backoff (`min(sleep * 2, 60)`) |
| `gridfs/main.py` | `CHANGE_STREAM_DB` | `pymongo` | `bigfiles` (`20MB_file` upload, copy, download to `20MB_file_python`, `readchunk()`) |
| `csfle/main.py` | `DB` | `pymongo[encryption]` | `encryption.__CSFLEExampleKeyVault`, `test.orders_encrypted` (`example_key_1`, `example_key_2`) |
| `qe/main.py` | `DB` | `pymongo[encryption]` | `encryption.__QEExampleKeyVault`, `shop.orders_encrypted` (equality query on `credit_card.number`) |
| `exercises/exercise_1_5.py` | `DB` | `pymongo[encryption]` | `bigfiles["fs.files"].watch()` (`ServerApi("1")`, `operationType: insert`) |
| `exercises/exercise_4_4.py` | `DB` | `pymongo[encryption]` | `encryption.__CSFLEExampleKeyVault`, `test.users` (`email_key` deterministic, `ssn_key` random) |

## JavaScript Collection Scripts and Datasets

| Artifact | Purpose | Target Collection / Database |
| :--- | :--- | :--- |
| `clustered_collections/create_clustered_collection.js` | Creates clustered index on `_id` | `stocksMDBClustered` |
| `materialized_views/create_view.js` | `$project`, `$group`, `$merge` daily averages | `stocks` -> `stocksDailyAvgView` |
| `materialized_views/data_change.js` | Inserts new `MDB` stock record (`price: 222.22`) | `stocks` |
| `materialized_views/update_view.js` | Incremental `$merge` (`whenMatched: "replace"`, `whenNotMatched: "insert"`) | `stocksDailyAvgView` |
| `timeseries/create_timeseries_collection.js` | Creates hourly time-series collection (`timeField: "ts"`, `metaField: "ticker"`) | `stocks_timeseries` |
| `timeseries/add_stock_data.js` | Bulk inserts hourly stock data points | `stocks_timeseries` |
| `timeseries/sample_query.js` | Daily stock average aggregation | `stocks_timeseries` |
| `views/sample_query.js` | Standard read-only aggregation view | `stocks` -> `stocksDailyAvg` |
| `datasets/script` | Runs `mongoimport --port 27018 --db=test` | `filme.json`, `stocks.json`, `orders.json`, `books.json` |
