#!/usr/bin/env python3
"""Bangun ulang poster berita 21 Nov 2026 dari aset teks di repo ini.

Posternya berupa PNG 1024x1024, tapi transport snapshot hanya membawa
teks UTF-8 — jadi gambar itu disimpan sebagai satu baris base64 di
``assets/poster.png.b64``. Skrip ini mengubah baris itu kembali menjadi
PNG, menyimpan salinan lokal di samping skrip bila belum ada atau isinya
sudah tidak sama, lalu menaruh hasil akhirnya di
``$MAKEFUN_OUTPUT_DIR/entry.png``.

Satu-satunya tulisan ke dalam repo adalah salinan lokal ``poster.png``
itu sendiri, dan itu pun hanya bila berkasnya hilang atau berbeda — dan
bila repo sedang read-only, langkah itu dilewati saja tanpa menggagalkan
jalan. Hasil akhir selalu ditulis dari byte yang sudah divalidasi,
langsung ke direktori output.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import sys
from pathlib import Path

# Poster yang diminta bounty: 1024x1024, tepat 711042 byte.
UKURAN_HARUS = 711042
# Delapan byte pertama setiap berkas PNG.
TANDA_PNG = b"\x89PNG\r\n\x1a\n"

# Nama-nama relatif terhadap direktori tempat berkas ini berada.
ASET_REL = Path("assets") / "poster.png.b64"
POSTER_REL = Path("poster.png")
ENTRY_REL = Path("entry.png")


def akar_skrip() -> Path:
    """Direktori yang memuat berkas ini; root repo saat dijalankan."""
    return Path(__file__).resolve().parent


def muat_byte_gambar(aset: Path) -> bytes:
    """Kembalikan byte PNG yang tersembunyi di dalam aset base64.

    FileNotFoundError bila asetnya tidak ada, ValueError bila isinya
    bukan base64 yang valid.
    """
    teks = aset.read_text(encoding="ascii").strip()
    try:
        return base64.b64decode(teks, validate=True)
    except binascii.Error as exc:
        raise ValueError(f"aset {aset} bukan base64 valid: {exc}") from exc


def periksa_gambar(blob: bytes) -> None:
    """Tolak apa pun yang bukan poster yang persis kita harapkan."""
    if blob[:8] != TANDA_PNG:
        raise ValueError("byte hasil decode tidak diawali tanda PNG")
    if len(blob) != UKURAN_HARUS:
        raise ValueError(
            f"poster hasil decode {len(blob)} byte, harusnya {UKURAN_HARUS}"
        )

def segarkan_poster(blob: bytes, poster: Path) -> str:
    """Pastikan ``poster`` di disk berisi ``blob``.

    Kembalikan "ditulis" bila berkasnya baru dibuat/diubah, "sudah ada"
    bila isinya memang sudah sama, dan "dilewati" bila repo tidak bisa
    ditulis (misalnya checkout read-only) — yang terakhir ini bukan
    kegagalan, karena hasil akhir tidak bergantung pada salinan lokal.
    """
    try:
        if poster.is_file() and poster.read_bytes() == blob:
            return "sudah ada"
        poster.write_bytes(blob)
        return "ditulis"
    except OSError:
        return "dilewati"


def terbitkan(blob: bytes, tujuan_dir: Path) -> Path:
    """Tulis ``entry.png`` ke direktori output dari byte yang tervalidasi."""
    tujuan_dir.mkdir(parents=True, exist_ok=True)
    tujuan = tujuan_dir / ENTRY_REL
    tujuan.write_bytes(blob)
    return tujuan


def sidik(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def jalan(argv: list[str]) -> int:
    akar = akar_skrip()
    aset = akar / ASET_REL
    poster = akar / POSTER_REL
    keluar = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or akar)

    try:
        blob = muat_byte_gambar(aset)
        periksa_gambar(blob)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"galat: {exc}", file=sys.stderr)
        return 1

    try:
        status = segarkan_poster(blob, poster)
        tujuan = terbitkan(blob, keluar)
    except OSError as exc:
        print(f"galat: tidak bisa menulis output: {exc}", file=sys.stderr)
        return 1

    print(f"poster: {len(blob)} byte sha256={sidik(blob)}")
    print(f"salinan lokal: {poster} ({status})")
    print(f"entry: {tujuan}")
    return 0


if __name__ == "__main__":
    raise SystemExit(jalan(sys.argv[1:]))
