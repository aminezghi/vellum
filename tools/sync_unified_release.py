#!/usr/bin/env python3
"""Sync and unify GitHub Release v2.1.0 assets and description."""

import json
import os
import subprocess
import time
import urllib.request

REPO = "aminezghi/vellum"
RELEASE_TAG = "v2.1.0"

NEW_ASSETS = [
    "Vellum-Desktop-v2.1.0-macOS.dmg",
    "Vellum-Desktop-v2.1.0-macOS.zip",
    "Vellum-Desktop-v2.1.0-Windows-x64.exe",
    "Vellum-Desktop-v2.1.0-Windows-x64.zip",
    "Vellum-Web-v2.1.0-macOS.zip",
    "Vellum-Web-v2.1.0-Windows-x64.zip",
    "DISTRIBUTABLES/SHA256SUMS.txt",
]


def get_token() -> str:
    cred = subprocess.check_output(
        ["git", "credential", "fill"],
        input=b"protocol=https\nhost=github.com\n\n",
    ).decode()
    for line in cred.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("Could not retrieve GitHub token.")


def main():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Vellum-Release-Agent",
        "Accept": "application/vnd.github.v3+json",
    }

    # 1. Fetch release info
    print(f"Fetching release {REPO} {RELEASE_TAG}...")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/tags/{RELEASE_TAG}",
        headers=headers,
    )
    with urllib.request.urlopen(req) as resp:
        release = json.load(resp)

    release_id = release["id"]
    upload_url_base = f"https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets"
    existing_assets = {a["name"]: a["id"] for a in release.get("assets", [])}

    # Target asset basenames we want to keep/upload
    target_names = {os.path.basename(p) for p in NEW_ASSETS}

    # Delete any asset that is NOT in target_names or has old naming
    for name, asset_id in existing_assets.items():
        if name not in target_names:
            print(f"Deleting outdated asset: {name} (ID: {asset_id})...")
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/releases/assets/{asset_id}",
                headers=headers,
                method="DELETE",
            )
            try:
                with urllib.request.urlopen(del_req) as del_resp:
                    print(f"Deleted {name}.")
            except Exception as e:
                print(f"Error deleting {name}: {e}")

    # Re-fetch remaining assets
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases/tags/{RELEASE_TAG}",
        headers=headers,
    )
    with urllib.request.urlopen(req) as resp:
        release = json.load(resp)
    current_assets = {a["name"]: a["id"] for a in release.get("assets", [])}

    # Upload missing or updated assets
    for file_path in NEW_ASSETS:
        basename = os.path.basename(file_path)
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found on disk, skipping.")
            continue

        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)

        if basename in current_assets:
            print(f"Asset {basename} already exists on release, deleting to replace with fresh build...")
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{REPO}/releases/assets/{current_assets[basename]}",
                headers=headers,
                method="DELETE",
            )
            with urllib.request.urlopen(del_req):
                print(f"Deleted old {basename}.")

        print(f"Uploading {basename} ({size_mb:.1f} MB)...")
        upload_url = f"{upload_url_base}?name={basename}"

        upload_headers = dict(headers)
        if basename.endswith(".txt"):
            upload_headers["Content-Type"] = "text/plain; charset=utf-8"
        elif basename.endswith(".dmg"):
            upload_headers["Content-Type"] = "application/x-apple-diskimage"
        elif basename.endswith(".exe"):
            upload_headers["Content-Type"] = "application/x-msdownload"
        else:
            upload_headers["Content-Type"] = "application/zip"
        upload_headers["Content-Length"] = str(file_size)

        t0 = time.time()
        with open(file_path, "rb") as f:
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
                print(f"Uploaded {basename} successfully! ID: {res.get('id')} in {elapsed:.1f}s ({speed_mb:.2f} MB/s)")

    print("All release assets synchronized successfully!")


if __name__ == "__main__":
    main()
