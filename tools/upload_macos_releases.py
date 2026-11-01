#!/usr/bin/env python3
"""Upload macOS release bundles to GitHub Releases v2.1.0."""

import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "aminezghi/vellum"
RELEASE_TAG = "v2.1.0"
FILES_TO_UPLOAD = [
    "Vellum_Desktop_macOS.zip",
    "Vellum_Web_macOS.zip",
]


def get_token() -> str:
    cred = subprocess.check_output(
        ["git", "credential", "fill"],
        input=b"protocol=https\nhost=github.com\n\n",
    ).decode()
    for line in cred.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("Could not retrieve GitHub token from git credentials.")


def main():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Vellum-Release-Agent",
        "Accept": "application/vnd.github.v3+json",
    }

    # 1. Fetch release metadata
    print(f"Fetching release metadata for {REPO} {RELEASE_TAG}...")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/tags/{RELEASE_TAG}",
        headers=headers,
    )
    with urllib.request.urlopen(req) as resp:
        release = json.load(resp)

    release_id = release["id"]
    upload_url_base = f"https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets"
    existing_assets = {a["name"]: a["id"] for a in release.get("assets", [])}

    for filename in FILES_TO_UPLOAD:
        if not os.path.exists(filename):
            print(f"Warning: {filename} does not exist on disk, skipping.")
            continue

        file_size = os.path.getsize(filename)
        size_mb = file_size / (1024 * 1024)

        if filename in existing_assets:
            asset_id = existing_assets[filename]
            print(f"Asset {filename} already exists (ID: {asset_id}), deleting old version...")
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/releases/assets/{asset_id}",
                headers=headers,
                method="DELETE",
            )
            with urllib.request.urlopen(del_req) as del_resp:
                print(f"Deleted old {filename}.")

        print(f"Uploading {filename} ({size_mb:.1f} MB)...")
        upload_url = f"{upload_url_base}?name={filename}"

        upload_headers = dict(headers)
        upload_headers["Content-Type"] = "application/zip"
        upload_headers["Content-Length"] = str(file_size)

        t0 = time.time()
        with open(filename, "rb") as f:
            up_req = urllib.request.Request(
                upload_url,
                data=f,
                headers=upload_headers,
                method="POST",
            )
            with urllib.request.urlopen(up_req) as up_resp:
                res = json.load(up_resp)
                elapsed = time.time() - t0
                speed_mb = size_mb / elapsed if elapsed > 0 else 0
                print(f"Uploaded {filename} successfully! ID: {res.get('id')} in {elapsed:.1f}s ({speed_mb:.2f} MB/s)")

    print("All release assets processed successfully!")


if __name__ == "__main__":
    main()
