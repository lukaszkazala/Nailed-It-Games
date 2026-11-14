"""Oblicza SHA-256 pliku modelu lub porównuje go z zaufanym hashem."""

import argparse
import hashlib
import re
from pathlib import Path


def sha256_file(path):
    """Liczy skrót dokładnych bajtów pliku, łącznie z końcami linii."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="plik do sprawdzenia, np. main.py")
    parser.add_argument("--verify", metavar="SHA256", help="zaufany hash referencyjny")
    args = parser.parse_args()

    if args.verify is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", args.verify):
        parser.error("SHA-256 musi zawierać dokładnie 64 znaki szesnastkowe.")

    try:
        actual_hash = sha256_file(args.file)
    except OSError as error:
        parser.error(str(error))

    if args.verify is None:
        print(actual_hash)
        return 0

    expected_hash = args.verify.lower()
    if actual_hash == expected_hash:
        print(f"SHA-256 zgodny: {args.file}")
        return 0

    print(f"SHA-256 niezgodny: {args.file}")
    print(f"Oczekiwany: {expected_hash}")
    print(f"Obliczony:  {actual_hash}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
