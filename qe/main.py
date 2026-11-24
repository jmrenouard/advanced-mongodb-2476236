import base64
import binascii
import os
import pymongo

from pymongo.encryption import (ClientEncryption)
from pymongo.encryption_options import AutoEncryptionOpts
from bson.codec_options import CodecOptions
from bson.binary import STANDARD


def load_local_master_key(path='local_keyfile'):
    """Read local master key file, decoding base64 text produced by helper script."""
    with open(path, 'rb') as key_file:
        raw = key_file.read()
    if len(raw) == 96:
        return raw
    stripped = raw.strip()
    if len(stripped) == 96:
        return stripped
    try:
        decoded = base64.b64decode(stripped, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("local_keyfile must contain 96 raw bytes or valid base64") from exc
    if len(decoded) != 96:
        raise ValueError("Decoded local_keyfile must be 96 bytes")
    return decoded


def main():
    local_main_key = load_local_master_key('local_keyfile')
    kms_providers = {"local": {"key": local_main_key}}

    # The MongoDB namespace (db.collection) used to store
    # the data encryption keys.
    key_vault_namespace = "encryption.__QEExampleKeyVault"

    auto_encryption_opts = AutoEncryptionOpts(
        kms_providers, key_vault_namespace)

    client = pymongo.MongoClient(os.environ['DB'], auto_encryption_opts=auto_encryption_opts)

    # Drops these collections if they exist so you can rerun this script:
    # - "encryption.__keyVault"
    # - "shop.orders_encrypted"
    client["encryption"]["__keyVault"].drop()
    client["shop"]["orders_encrypted"].drop()

    # Document to be inserted
    document = {
        "name": "Naomi Pentrel",
        "email": "naomi@email.com",
        "address": {
            "street": "Sample Street 123",
            "zip": "1234AB",
            "country": "Netherlands"
        },
        "credit_card": { "type": "maestro", "number": "0604871496158803" },
        "items": [ { "book_id": "183408230-7", "price": 25.99 } ]
    }

    encrypted_fields_map = {
        "fields": [
            {
                "path": "address",
                "bsonType": "object",
                # Cannot be queried on with this configuration
            },
            {
                "path": "credit_card.number",
                "bsonType": "string",
                # Can be queried on
                "queries": [{"queryType": "equality"}]
            }
        ]
    }

    # Create the client with the information for creating an encrypted collection

    try:
        client_encryption = ClientEncryption(
            kms_providers=kms_providers,
            key_vault_namespace=key_vault_namespace,
            key_vault_client=client,
            codec_options=CodecOptions(uuid_representation=STANDARD)
        )
    except Exception as e:
        raise Exception("Exception creating encrypted client: ", e)

    # Create the new collection that is capable of Queryable Encryption

    try:
        client_encryption.create_encrypted_collection(
            client.shop,
            "orders_encrypted",
            encrypted_fields_map,
            kms_provider="local",
        )
    except Exception as e:
        raise Exception("Exception creating encrypted collection: ", e)

    coll = client.shop.orders_encrypted
    coll.insert_one(document)

    # Automatically decrypts any encrypted fields.
    doc = coll.find_one()
    print('Decrypted document: %s' % (doc))

    # Show unencrypted document by queried from a MongoClient without auto_encryption_opts
    unencrypted_client = pymongo.MongoClient(os.environ['DB'])
    unencrypted_coll = unencrypted_client.shop.orders_encrypted
    print('Encrypted document: %s' % (unencrypted_coll.find_one()))

    # Cleanup resources.
    client_encryption.close()
    client.close()
    unencrypted_client.close()


if __name__ == "__main__":
    main()
