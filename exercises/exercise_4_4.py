# Based on https://pymongo.readthedocs.io/en/stable/examples/encryption.html

import base64
import binascii
import os
import pymongo

from pymongo.encryption import (Algorithm,
                                ClientEncryption)
from pymongo.encryption_options import AutoEncryptionOpts


def load_local_master_key(path='../csfle/local_keyfile'):
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


def encrypt_fields(client_encryption, document):
    if "email" in document:
        encrypted_email = client_encryption.encrypt(
            document["email"],
            Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Deterministic,
            key_alt_name='email_key')
        document["email"] = encrypted_email

    if "ssn" in document:
        encrypted_ssn = client_encryption.encrypt(
            document["ssn"],
            Algorithm.AEAD_AES_256_CBC_HMAC_SHA_512_Random,
            key_alt_name='ssn_key')
        document["ssn"] = encrypted_ssn

    return document


def main():
    local_main_key = load_local_master_key('../csfle/local_keyfile')
    kms_providers = {"local": {"key": local_main_key}}

    # The MongoDB namespace (db.collection) used to store
    # the encryption data keys.
    key_vault_namespace = "encryption.__CSFLEExampleKeyVault"

    # bypass_auto_encryption=True disable automatic encryption but keeps
    # the automatic _decryption_ behavior. bypass_auto_encryption will
    # also disable spawning mongocryptd.
    auto_encryption_opts = AutoEncryptionOpts(
        kms_providers, key_vault_namespace, bypass_auto_encryption=True)

    client = pymongo.MongoClient(os.environ['DB'], auto_encryption_opts=auto_encryption_opts)
    coll = client.test.users

    client_encryption = ClientEncryption(
        kms_providers,
        key_vault_namespace,
        # The MongoClient to use for reading/writing to the key vault.
        # This can be the same MongoClient used by the main application.
        client,
        # The CodecOptions class used for encrypting and decrypting.
        # This should be the same CodecOptions instance you have configured
        # on MongoClient, Database, or Collection.
        coll.codec_options)

    # Create new data keys
    client_encryption.create_data_key(
        'local', key_alt_names=['email_key'])

    client_encryption.create_data_key(
        'local', key_alt_names=['ssn_key'])

    document = {
        "name": "Naomi Pentrel",
        "email": "naomi@email.com",
        "ssn": "12345678",
        "username": "n2231512"
    }

    document = encrypt_fields(client_encryption, document)
    coll.insert_one(document)

    # Automatically decrypts any encrypted fields.
    doc = coll.find_one()
    print('Decrypted document: %s' % (doc))

    unencrypted_coll = pymongo.MongoClient(os.environ['DB']).test.users
    print('Encrypted document: %s' % (unencrypted_coll.find_one()))

    # Cleanup resources.
    client_encryption.close()
    client.close()


if __name__ == "__main__":
    main()
