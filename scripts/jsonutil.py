#!/usr/bin/env python3
import sys, json, gzip

def load_bytes(b: bytes):
    # plain json
    try:
        return json.loads(b.decode("utf-8", errors="strict"))
    except Exception:
        pass
    # gzip json
    try:
        return json.loads(gzip.decompress(b).decode("utf-8", errors="strict"))
    except Exception:
        pass
    # last resort
    return json.loads(b.decode("utf-8", errors="replace"))

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
