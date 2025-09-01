import zipfile
import zlib
from .read_bytes import ReadBytes


def is_probably_reversed(data: bytes) -> bool:
    reversed_snippets = [b'}', b'eman', b'tamrof', b'ezis']
    png_signature = b'\x89PNG\r\n\x1a\n'

    if all(s in data.lower() for s in reversed_snippets):
        return True

    if data.startswith(png_signature):
        return True

    return False


def convert(file):
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                with zip_ref.open(file_info) as f:
                    data = f.read()
                    yield file_info.filename, data
    except zipfile.BadZipFile:
        with open(file, 'rb') as f:
            data = f.read()

        read_bytes = ReadBytes(data)

        file_count = read_bytes.read_short()
        if file_count <= 0:
            file_count = read_bytes.read_short()

        for _ in range(file_count):
            name = read_bytes.read_string()
            length = read_bytes.read_int()
            compressed = read_bytes.read_bytes(length)
            if compressed.startswith(b'x\x9c'):
                decompressor = zlib.decompressobj()
            elif compressed.startswith(b'\x1f\x8b\x08'):
                decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            else:
                print(f"Unkwown compression format for {name}")
                continue

            try:
                decompressed = decompressor.decompress(compressed) + decompressor.flush()

                if is_probably_reversed(decompressed):
                    decompressed = decompressed[::-1]

                yield name, decompressed

            except zlib.error as e:
                print(f"Error decompressing {name}: {e}")


def save(file, r):
    with open(file, "wb") as f:
        f.write(r)
