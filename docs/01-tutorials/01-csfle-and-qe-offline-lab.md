# Tutorial 01: CSFLE and Queryable Encryption Offline Lab

In this tutorial, you generate a disposable 96-byte local master key in `/tmp`, verify key decoding, and test `csfle/main.py` offline without a live MongoDB server.

## Prerequisites

- Python 3.10+ (`python --version`)
- Optional `pymongo[encryption]` installed when running against live MongoDB (`pip install -r csfle/requirements.txt`)
- Local repository clone cleanly checked out

## Step 1 — Compile All Python Lab Scripts

Verify syntax across every Python module in the repository:

```bash
python -B -m py_compile change-streams/main.py change-streams/change_stream.py \
  change-streams/change_stream_2.py change-streams/resumable_change_stream.py \
  csfle/main.py qe/main.py gridfs/main.py exercises/exercise_1_5.py exercises/exercise_4_4.py
```

Expected result: exit code `0` with no `SyntaxError` output.

## Step 2 — Generate a Disposable Local Key and Test 96-Byte Decoding

Run the key generation helper inside `/tmp` and verify that `load_local_master_key()` decodes the base64 output into exactly `96` bytes:

```bash
echo $(head -c 96 /dev/urandom | base64 | tr -d '\n') > /tmp/test_local_keyfile
python -W default -B -c "import importlib.util, types, sys; \
  sys.modules.setdefault('pymongo', types.SimpleNamespace()); \
  sys.modules.setdefault('pymongo.encryption', types.SimpleNamespace(Algorithm=types.SimpleNamespace(), ClientEncryption=object)); \
  sys.modules.setdefault('pymongo.encryption_options', types.SimpleNamespace(AutoEncryptionOpts=object)); \
  spec = importlib.util.spec_from_file_location('csfle_main', 'csfle/main.py'); \
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); \
  key = m.load_local_master_key('/tmp/test_local_keyfile'); print('KEY_LEN', len(key))"
rm -f /tmp/test_local_keyfile
```

Expected output:

```text
KEY_LEN 96
```

## Step 3 — Run the Automated Offline Unit Suite

Run the full mocked test suite (`encrypt_fields`, key normalization, dataset validation, sharded configs, and Diátaxis checks):

```bash
python -B -m unittest discover -s tests -p "test_*.py" -v
```

## Next Steps

- Inspect JSON datasets and collection scripts in [Tutorial 02](02-change-streams-and-collections-lab.md).
- Configure real lab keys securely in [Configure Keys and Encryption Labs](../02-how-to-guides/01-configure-keys-and-run-encryption-labs.md).
- Inspect environment variables in [Modules, Env Vars, and Datasets](../03-reference/01-modules-env-vars-and-datasets.md).
- Compare explicit vs automatic encryption in [CSFLE vs Queryable Encryption](../04-explanation/01-csfle-vs-queryable-encryption-and-change-streams.md).
