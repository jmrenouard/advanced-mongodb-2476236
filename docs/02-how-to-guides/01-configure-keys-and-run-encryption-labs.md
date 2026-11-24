# Configure Keys and Run Encryption Labs

This guide tells how to generate `local_keyfile` secrets and run the `csfle`, `qe`, and `exercise_4_4.py` scripts.

**Prerequisites:**

- You must have Python 3.10+ with `pymongo[encryption]` and `crypt_shared` (or `mongocryptd`) installed.
- You must have a writable MongoDB instance URI set in the `DB` environment variable.
- You must have standard shell tools (`head`, `base64`, and `tr`) installed on Linux or WSL.

WARNING: DO NOT COMMIT GENERATED `local_keyfile` FILES TO VERSION CONTROL. LEAKED MASTER KEYS CAN DECRYPT STORED FIELD VALUES.

CAUTION: DO NOT RUN `qe/main.py` AGAINST A PRODUCTION DATABASE. THE SCRIPT DROPS `encryption.__keyVault` AND `shop.orders_encrypted` AT STARTUP.

## Procedure

1. Open the `csfle` folder and generate `local_keyfile`.

   ```bash
   cd csfle && bash ./script
   ```

2. Restrict file permissions on `csfle/local_keyfile` to owner read/write (`0600`).

   ```bash
   chmod 0600 local_keyfile
   ```

3. Export your lab MongoDB URI in the `DB` variable.

   ```bash
   export DB="mongodb://localhost:27017/"
   ```

4. Run the CSFLE example script inside `csfle/`.

   ```bash
   python main.py
   ```

5. If you run the Queryable Encryption lab, generate `qe/local_keyfile` and run `qe/main.py`.

   ```bash
   cd ../qe && bash ./script && chmod 0600 local_keyfile && python main.py
   ```

NOTE: The `exercises/exercise_4_4.py` script reads `../csfle/local_keyfile` relative to the `exercises/` directory.

## Verification

1. Confirm that both `Decrypted document:` and `Encrypted document:` lines print to stdout.

2. Verify that Git ignores any generated `local_keyfile` artifacts.

   ```bash
   git status --short
   ```

## Rollback

Remove generated local key files and drop temporary test collections after lab completion:

```bash
rm -f csfle/local_keyfile qe/local_keyfile
```

## References

- Environment variables and requirements: [Modules, Env Vars, and Datasets](../03-reference/01-modules-env-vars-and-datasets.md)
- Encryption architecture notes: [CSFLE vs Queryable Encryption](../04-explanation/01-csfle-vs-queryable-encryption-and-change-streams.md)
