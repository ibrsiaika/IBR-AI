#!/usr/bin/env python3
"""
Download MUCH more Python code via direct parquet file download (bypasses HF API rate limits).
- Downloads 1 parquet file (~50MB) of codeparrot/codeparrot-clean
- Filters & dedups to ~30K high-quality Python samples
- Adds high-quality web-scanning code patterns
- FREE — no auth, no payment
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent.parent / "research" / "big_code_dataset.json"
PARQUET_FILE = Path(__file__).resolve().parent.parent / "research" / "_codeparrot_0.parquet"
PARQUET_URL = "https://huggingface.co/api/datasets/codeparrot/codeparrot-clean/parquet/default/train/0.parquet"

UA = "Mozilla/5.0 (research-bot; contact: research@local)"


def download_parquet() -> bool:
    """Download 1 parquet file (~50MB) of codeparrot-clean."""
    if PARQUET_FILE.exists() and PARQUET_FILE.stat().st_size > 10_000_000:
        print(f"  parquet already exists: {PARQUET_FILE.stat().st_size/1024/1024:.1f} MB")
        return True
    print(f"  downloading {PARQUET_URL}...")
    req = urllib.request.Request(PARQUET_URL, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(PARQUET_FILE, "wb") as f:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0 and downloaded % (5 * 1024 * 1024) < 1024 * 256:
                    print(f"    {downloaded/1024/1024:.0f} / {total/1024/1024:.0f} MB")
        print(f"  downloaded: {PARQUET_FILE.stat().st_size/1024/1024:.1f} MB")
        return True
    except Exception as e:
        print(f"  download failed: {e}")
        return False


def clean_code(code: str) -> str | None:
    if not code:
        return None
    code = code.strip()
    if len(code) < 80 or len(code) > 5000:
        return None
    if not re.search(r"\b(def|class|import|from|return)\b", code):
        return None
    try:
        code.encode("ascii")
    except UnicodeEncodeError:
        return None
    lines = [l for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]
    if len(lines) < 4:
        return None
    # Skip huge boilerplate (license headers)
    if code.count("#") / max(len(code.split("\n")), 1) > 0.5:
        return None
    return code


WEB_SCAN_PATTERNS = [
    '''def scan_website(url, timeout=10):
    """Scan a website for common vulnerabilities."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Scanner/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        headers = dict(resp.headers)
        body = resp.read().decode("utf-8", errors="ignore")
        return {"status": resp.status, "headers": headers, "body_length": len(body)}
    except urllib.error.URLError as e:
        return {"error": str(e)}
''',
    '''def find_links(html):
    """Extract all href links from HTML."""
    import re
    pattern = r'<a[^>]+href=["\\']([^"\\']+)["\\']'
    return re.findall(pattern, html, re.IGNORECASE)
''',
    '''def check_security_headers(url):
    """Check security headers of a URL."""
    import urllib.request
    req = urllib.request.Request(url, method="HEAD")
    resp = urllib.request.urlopen(req)
    headers = dict(resp.headers)
    security = ["X-Frame-Options", "X-XSS-Protection", "X-Content-Type-Options",
                "Strict-Transport-Security", "Content-Security-Policy"]
    return {h: headers.get(h, "MISSING") for h in security}
''',
    '''def port_scan(host, ports=None, timeout=2):
    """Scan common ports on a host."""
    import socket
    if ports is None:
        ports = [21, 22, 80, 443, 8080, 8443, 3306, 5432]
    open_ports = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            open_ports.append(port)
        except (socket.timeout, ConnectionRefusedError):
            pass
        finally:
            sock.close()
    return open_ports
''',
    '''def crawl_page(url, max_depth=2, visited=None):
    """Crawl a webpage up to max_depth."""
    if visited is None:
        visited = set()
    if url in visited or max_depth < 0:
        return []
    visited.add(url)
    import urllib.request
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    found = [url]
    for link in find_links(html):
        if link.startswith("http"):
            found.extend(crawl_page(link, max_depth - 1, visited))
    return found
''',
    '''def detect_xss(html):
    """Detect potential XSS vectors in HTML."""
    import re
    patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on(error|load|click|mouseover)\\s*=",
    ]
    findings = []
    for p in patterns:
        matches = re.findall(p, html, re.IGNORECASE | re.DOTALL)
        findings.extend(matches)
    return findings
''',
    '''def detect_sqli(input_str):
    """Detect SQL injection patterns."""
    import re
    patterns = [
        r"('|\")\\s*(or|and)\\s+\\d+=\\d+",
        r"union\\s+select",
        r"--\\s*$",
        r";\\s*drop\\s+table",
        r"xp_cmdshell",
    ]
    return any(re.search(p, input_str, re.IGNORECASE) for p in patterns)
''',
    '''def banner_grab(host, port=80, timeout=5):
    """Grab service banner from host:port."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.send(b"HEAD / HTTP/1.0\\r\\n\\r\\n")
        banner = sock.recv(1024).decode("utf-8", errors="ignore")
        return banner
    except Exception as e:
        return str(e)
    finally:
        sock.close()
''',
    '''def fetch_robots_txt(url):
    """Fetch and parse robots.txt."""
    import urllib.request
    robots_url = url.rstrip("/") + "/robots.txt"
    try:
        resp = urllib.request.urlopen(robots_url, timeout=10)
        return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Error: {e}"
''',
    '''def analyze_response_time(url, n=5):
    """Measure response time statistics."""
    import urllib.request
    import time
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            urllib.request.urlopen(url, timeout=10)
            times.append(time.perf_counter() - t0)
        except Exception:
            pass
    if not times:
        return None
    return {"min": min(times), "max": max(times), "avg": sum(times)/len(times), "n": len(times)}
''',
    '''def extract_emails(text):
    """Extract email addresses from text."""
    import re
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
    return list(set(re.findall(pattern, text)))
''',
    '''def extract_ips(text):
    """Extract IPv4 addresses from text."""
    import re
    pattern = r"\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b"
    return list(set(re.findall(pattern, text)))
''',
    '''def check_subdomain_takeover(url):
    """Check for potential subdomain takeover."""
    import urllib.request
    fingerprints = ["NoSuchBucket", "Repository not found",
                    "no such app", "There isn't a GitHub Pages site here"]
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        body = resp.read().decode("utf-8", errors="ignore").lower()
        for fp in fingerprints:
            if fp.lower() in body:
                return {"vulnerable": True, "fingerprint": fp}
    except Exception as e:
        return {"error": str(e)}
    return {"vulnerable": False}
''',
    '''def dir_brute(url, wordlist=None):
    """Directory brute-force using common paths."""
    import urllib.request
    import urllib.error
    if wordlist is None:
        wordlist = ["admin", "login", "config", "backup", "test",
                    ".git", ".env", "wp-admin", "phpmyadmin", "api"]
    found = []
    for path in wordlist:
        full = f"{url.rstrip('/')}/{path}"
        try:
            resp = urllib.request.urlopen(full, timeout=5)
            found.append({"path": path, "status": resp.status})
        except urllib.error.HTTPError as e:
            if e.code != 404:
                found.append({"path": path, "status": e.code})
        except Exception:
            pass
    return found
''',
    '''def parse_http_headers(raw):
    """Parse raw HTTP headers string into dict."""
    lines = raw.split("\\r\\n")
    if not lines:
        return {}
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip()] = v.strip()
    return headers
''',
    '''def safe_request(url, retries=3, backoff=1.0):
    """Make HTTP request with retries and exponential backoff."""
    import urllib.request
    import urllib.error
    import time
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SafeBot/1.0"})
            return urllib.request.urlopen(req, timeout=10)
        except urllib.error.URLError as e:
            last_err = e
            time.sleep(backoff * (2 ** attempt))
    raise last_err
''',
]


def main() -> None:
    print("=" * 60)
    print("  IBR-GPT-Code — Download MUCH more data (parquet)")
    print("=" * 60)

    all_codes: list[str] = []

    # 1. Download parquet file
    print("\n[1/3] Downloading codeparrot parquet file...")
    if download_parquet():
        print("\n  Reading parquet & extracting Python code...")
        table = pq.read_table(PARQUET_FILE, columns=["content"])
        col = table.column("content").to_pylist()
        print(f"  total rows in parquet: {len(col):,}")
        accepted = 0
        for code in col:
            c = clean_code(code)
            if c:
                all_codes.append(c)
                accepted += 1
        print(f"  accepted (after clean): {accepted:,}")

    # 2. Add high-quality web-scanning code patterns
    print(f"\n[2/3] Adding {len(WEB_SCAN_PATTERNS)} web-scanning code patterns...")
    for p in WEB_SCAN_PATTERNS:
        all_codes.append(p)

    # 3. Merge with existing local data
    print("\n[3/3] Merge with existing local data (dedup)...")
    local_files = [
        Path(__file__).resolve().parent.parent / "research" / "large_code_dataset.json",
        Path(__file__).resolve().parent.parent / "research" / "code_cache_1000.json",
        Path(__file__).resolve().parent.parent / "research" / "cached_code_data.json",
    ]
    existing: set[str] = set()
    for lf in local_files:
        if lf.exists():
            with open(lf) as f:
                try:
                    d = json.load(f)
                    for s in d:
                        s_clean = clean_code(str(s))
                        if s_clean and s_clean not in existing:
                            existing.add(s_clean)
                except Exception as e:
                    print(f"  warn loading {lf.name}: {e}")
    print(f"  local unique: {len(existing):,}")
    for c in existing:
        if c not in all_codes:
            all_codes.append(c)

    # Final dedup
    seen: set[str] = set()
    deduped: list[str] = []
    for c in all_codes:
        if c not in seen:
            seen.add(c)
            deduped.append(c)

    total_chars = sum(len(c) for c in deduped)
    print(f"\n  Final: {len(deduped):,} unique samples | {total_chars:,} chars ({total_chars/1e6:.2f} MB)")

    with open(OUT, "w") as f:
        json.dump(deduped, f)
    print(f"  Saved: {OUT} ({OUT.stat().st_size/1024/1024:.2f} MB)")

    # Clean up parquet file to save disk
    try:
        PARQUET_FILE.unlink()
        print(f"  cleaned up {PARQUET_FILE.name}")
    except Exception:
        pass

    print(f"\n{'='*60}")
    print(f"DONE — {len(deduped):,} samples ready for training")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
