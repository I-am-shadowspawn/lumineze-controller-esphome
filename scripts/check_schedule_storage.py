"""Run storage fault injection and cross-check packed CRC with an independent library."""
from pathlib import Path
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    binary = Path(directory) / 'storage'
    record_file = Path(directory) / 'record.bin'
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    str(ROOT / 'tests/test_schedule_store.cpp'), '-o', str(binary)], check=True)
    subprocess.run([str(binary), str(record_file)], check=True)
    record = record_file.read_bytes()
    assert len(record) == 87
    assert record[:4] == b'LZSC'
    assert zlib.crc32(record[:83]) == int.from_bytes(record[83:], 'little')
print('PASS independent packed length and IEEE CRC-32; all torn-write prefixes exercised')
