"""Native proto generation script using grpc_tools.protoc.

Usage (from repo root, after creating/activating virtualenv and installing requirements):

    python generate_proto.py

Generates weather_pb2.py and weather_pb2_grpc.py into project root.
"""
from pathlib import Path
import sys
from grpc_tools import protoc

PROTO_DIR = Path('')
OUT_DIR = Path('..')
PROTO_FILE = 'weather.proto'

def main() -> int:
    proto_path = PROTO_DIR / PROTO_FILE
    if not proto_path.exists():
        print(f"Proto file not found: {proto_path}")
        return 1
    args = [
        'protoc',
        f'-I{PROTO_DIR}',
        f'--python_out={OUT_DIR}',
        f'--grpc_python_out={OUT_DIR}',
        str(proto_path)
    ]
    print('Running protoc with args:', ' '.join(args))
    result = protoc.main(args)
    if result == 0:
        print('Generation complete.')
    else:
        print('protoc failed with exit code', result)
    return result

if __name__ == '__main__':
    raise SystemExit(main())
