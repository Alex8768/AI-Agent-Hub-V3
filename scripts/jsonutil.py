#!/usr/bin/env python3
import sys, json, gzip

def load_bytes(b: bytes):
    # Robust loader: supports plain JSON and gzipped JSON (even with leading junk/CRLF).
    if not b:
        return json.loads("null")

    # Trim leading whitespace/newlines (sometimes present in buffers)
    bb = b.lstrip()

    # 1) plain json first (fast path)
    try:
        return json.loads(bb.decode("utf-8", errors="strict"))
    except Exception:
        pass

    # 2) gzip json (magic header 1f 8b)
    def try_gzip(buf: bytes):
        try:
            return json.loads(gzip.decompress(buf).decode("utf-8", errors="strict"))
        except Exception:
            return None

    if len(bb) >= 2 and bb[0] == 0x1F and bb[1] == 0x8B:
        got = try_gzip(bb)
        if got is not None:
            return got

    # 3) sometimes there is a small prefix before gzip stream; scan for magic
    idx = bb.find(b"\x1f\x8b")
    if idx != -1:
        got = try_gzip(bb[idx:])
        if got is not None:
            return got

    # 4) last resort (replace errors)
    return json.loads(bb.decode("utf-8", errors="replace"))

def main():
    if len(sys.argv) < 2:
        print("usage: jsonutil.py <len|get|pretty|export_id> [key]", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1]
    raw = sys.stdin.buffer.read()
    data = load_bytes(raw)

    if cmd == "len":
        print(len(data) if isinstance(data, list) else 0)
        return

    if cmd == "get":
        key = sys.argv[2] if len(sys.argv) > 2 else ""
        if isinstance(data, dict):
            print(data.get(key, ""))
        else:
            print("")
        return

    if cmd == "export_id":
        if isinstance(data, dict):
            meta = data.get("metadata") or {}
            if isinstance(meta, dict):
                print(meta.get("export_id", ""))
                return
        print("")
        return

    if cmd == "pretty":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print(f"unknown cmd: {cmd}", file=sys.stderr)
    sys.exit(2)

if __name__ == "__main__":
    main()
