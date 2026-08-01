from __future__ import annotations

import argparse
from pathlib import Path

from cryptography.fernet import Fernet


def load_or_create_key(key_path: Path) -> bytes:
    if key_path.exists():
        return key_path.read_bytes().strip()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    key_path.write_bytes(key)
    return key


def encrypt_file(input_path: Path, output_path: Path, key_path: Path) -> None:
    key = load_or_create_key(key_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    encrypted = Fernet(key).encrypt(input_path.read_bytes())
    output_path.write_bytes(encrypted)


def decrypt_file(input_path: Path, output_path: Path, key_path: Path) -> None:
    if not key_path.exists():
        raise FileNotFoundError(f"Key file not found: {key_path}")
    decrypted = Fernet(key_path.read_bytes().strip()).decrypt(input_path.read_bytes())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(decrypted)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt local env files without printing secret values."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    encrypt = subparsers.add_parser("encrypt", help="Encrypt an env file")
    encrypt.add_argument("--input", default=".env", help="Plaintext env file")
    encrypt.add_argument("--output", default=".env.enc", help="Encrypted output file")
    encrypt.add_argument("--key-file", default=".env.key", help="Local encryption key file")

    decrypt = subparsers.add_parser("decrypt", help="Decrypt an env file")
    decrypt.add_argument("--input", default=".env.enc", help="Encrypted input file")
    decrypt.add_argument("--output", default=".env", help="Plaintext output file")
    decrypt.add_argument("--key-file", default=".env.key", help="Local encryption key file")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    key_path = Path(args.key_file)

    if args.command == "encrypt":
        encrypt_file(input_path, output_path, key_path)
        print(f"Encrypted {input_path} -> {output_path}")
        print(f"Key file: {key_path}")
    else:
        decrypt_file(input_path, output_path, key_path)
        print(f"Decrypted {input_path} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
