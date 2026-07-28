# endcord - Copyright (C) 2025-2026 SparkLost. All Rights Reserved.
# Source-available under the Endcord License. See LICENSE for terms.
# Redistribution of modified versions is not permitted.

IMAGE = "image/"
VIDEO = "video/"
AUDIO = "audio/"


def guess(obj):
    """Try to gues file type based on its magic nuber, fallback to checking extension, only image video and audio types are implemented"""
    if not obj:
        return None

    if isinstance(obj, str):
        with open(obj, "rb") as fp:
            buf = bytearray(fp.read(132))
    elif isinstance(obj, bytearray):
        buf = bytearray[:132 if len(obj) > 132 else len(obj)]
    elif isinstance(obj, bytes):
        buf = bytearray[:132 if len(obj) > 132 else len(obj)]
    elif isinstance(obj, memoryview):
        buf = bytearray(bytearray[:132 if len(obj) > 132 else len(obj)].tolist())
    else:
        return None

    # IMAGE
    if buf[:3] == b"\xff\xd8\xff":   # jpeg
        return IMAGE + "jpeg"
    if buf[:8] == b"\x89PNG\r\n\x1a\n":   # png and apng
        i = 8
        buf_len = len(buf)
        while i + 8 <= buf_len:
            data_length = int.from_bytes(buf[i:i+4], byteorder="big")
            chunk_type = buf[i+4:i+8]
            if chunk_type in (b"IDAT", b"IEND"):
                break
            if chunk_type == b"acTL":
                return IMAGE + "apng"
            i += 12 + data_length
        return IMAGE + "png"
    if buf[:3] == b"GIF":   # gif
        return IMAGE + "gif"
    if buf[:4] == b"RIFF" and buf[8:14] == b"WEBPVP":   # webp
        return IMAGE + "webp"
    if buf[:2] == b"BM":   # bmp
        return IMAGE + "bmp"
    if buf[:4] == b"\x00\x00\x01\x00":
        return IMAGE + "x-icon"
    if buf[:2] == b"\xff\x0a" or buf[:12] == b"\x00\x00\x00\x0cJXL \r\n\x87\n":   # jxl
        return IMAGE + "jxl"
    if buf[:4] == b"\x00\x00\x00\x0c" and buf[16:24] == b"ftypjp2 ":   # jpx
        return IMAGE + "jpx"
    if buf[:4] in (b"II*\x00", b"MM\x00*"):   # cr2 and tiff
        if buf[8:10] == b"CR":
            return IMAGE + "x-canon-cr2"
        return IMAGE + "tiff"
    if buf[:4] == b"qoif":
        return IMAGE + "qoi"
    if buf[:4] == b"DDS ":
        return IMAGE + "dds"
    if buf[4:8] == b"ftyp":
        ftyp_len = int.from_bytes(buf[0:4], byteorder="big")
        major_brand = buf[8:12].decode(errors="ignore")
        if major_brand in ("avif", "avis"):
            return IMAGE + "avif"
        if major_brand == "heic":
            return IMAGE + "heic"
        if major_brand in ("mif1", "msf1"):
            compatible_brands = []
            for i in range(16, ftyp_len, 4):
                compatible_brands.append(buf[i:i+4].decode(errors="ignore"))
            if "avif" in compatible_brands:
                return IMAGE + "avif"
            if "heic" in compatible_brands:
                return IMAGE + "heic"

    # VIDEO
    if buf.startswith(b"\x1A\x45\xDF\xA3"):
        search_buf = buf[:4096]
        if b"\x42\x82\x88matroska" in search_buf:   # mkv
            return VIDEO + "x-matroska"
        if b"\x42\x82\x84webm" in search_buf:   # webm
            return VIDEO + "webm"
    if buf[:4] == b"\x00\x00\x00\x1c" and buf[4:11] == b"ftypM4V":   # m4v
        return VIDEO + "x-m4v"
    if buf[:4] == b"RIFF" and buf[8:12] == b"AVI ":   # avi
        return VIDEO + "x-msvideo"
    if buf[:10] == b"\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9":   # wmv
        return VIDEO + "x-ms-wmv"
    if buf[:4] == b"FLV\x01":   # flv
        return VIDEO + "x-flv"
    if buf[:3] == b"\x00\x00\x01" and buf[3:4]:   # mpeg
        if 0xB0 <= buf[3] <= 0xBF:
            return VIDEO + "mpeg"
    if buf[4:11] == b"ftyp3gp":   # 3gp
        return VIDEO + "3gpp"
    if buf[4:8] == b"ftyp":   # iso-bmf: mp4 and mov
        ftyp_len = int.from_bytes(buf[0:4], byteorder="big")
        major_brand = buf[8:12].decode(errors="ignore")
        if major_brand == "qt  ":   # mov
            return VIDEO + "quicktime"
        if major_brand in ("mp41", "mp42", "isom"):   # mp4
            return VIDEO + "mp4"
        for i in range(16, ftyp_len, 4):   # mp4
            brand = buf[i:i+4].decode(errors="ignore")
            if brand in ("mp41", "mp42", "isom"):
                return VIDEO + "mp4"

    # AUDIO
    if buf[:3] == b"ID3" or (buf[0] == 0xFF and buf[1] in (0xE2, 0xE3, 0xF2, 0xF3, 0xFA, 0xFB)):   # mp3
        return AUDIO + "mpeg"
    if buf[4:11] == b"ftypM4A" or buf[:4] == b"M4A ":   # m4a
        return AUDIO + "mp4"
    if buf[:4] == b"RIFF" and buf[8:12] == b"WAVE":   # wav
        return AUDIO + "x-wav"
    if buf[:4] == b"OggS":   # ogg
        return AUDIO + "ogg"
    if buf[:4] == b"fLaC":   # flac
        return AUDIO + "x-flac"
    if buf[:2] in (b"\xff\xf1", b"\xff\xf9"):   # aac
        return AUDIO + "aac"
    if buf[:4] == b"FORM" and buf[8:12] == b"AIFF":   # aiff
        return AUDIO + "x-aiff"
    if buf[:6] == b"#!AMR\n":   # amr
        return AUDIO + "amr"
    if buf[:4] == b"MThd":   # midi
        return AUDIO + "midi"

    # FALLBACK TO EXTENSION
    if isinstance(obj, str):
        import mimetypes
        return mimetypes.guess_type(obj)[0]
    return None
