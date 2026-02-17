#!/usr/bin/env python3
"""
Push Logistics files to GitHub via REST API
Works without local git setup
"""

import os
import base64
import subprocess

# USER MUSS DAS HIER ANPASSEN:
GITHUB_TOKEN = "ghp_YOUR_NEW_TOKEN_HERE"  # ← Dein neuer Token!
REPO = "73sero/Logistik"
BRANCH = "main"

FILES_TO_PUSH = [
    ("logistik_api.py", "logistik_api.py"),
    ("logistik_db.py", "logistik_db.py"),
    ("logistik.db", "logistik.db"),
    ("workflow_engine.py", "workflow_engine.py"),
    ("agent_prompts.md", "agent_prompts.md"),
    ("logistik_db_schema.sql", "logistik_db_schema.sql"),
    ("README_LOGISTICS_SYSTEM.md", "README_LOGISTICS_SYSTEM.md"),
    ("SETUP.md", "SETUP.md"),
    ("START_SYSTEM.py", "START_SYSTEM.py"),
    ("requirements.txt", "requirements.txt"),
    ("dashboard/index.html", "dashboard/index.html"),
]

def push_file_to_github(filepath, github_path, token):
    """Push single file to GitHub using REST API"""
    
    # Read file
    with open(filepath, 'rb') as f:
        content = f.read()
    
    # Encode to base64
    content_b64 = base64.b64encode(content).decode()
    
    # GitHub API call
    url = f"https://api.github.com/repos/{REPO}/contents/{github_path}"
    
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "message": f"Add {os.path.basename(github_path)}",
        "content": content_b64,
        "branch": BRANCH
    }
    
    import json
    import urllib.request
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=headers,
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            if 'content' in result:
                print(f"✅ {github_path}")
                return True
            else:
                print(f"❌ {github_path}: {result}")
                return False
    except Exception as e:
        print(f"❌ {github_path}: {e}")
        return False

def main():
    if GITHUB_TOKEN == "ghp_YOUR_NEW_TOKEN_HERE":
        print("🛑 STOP!")
        print("\n⚠️  Du musst zuerst einen NEUEN GitHub Token erstellen:")
        print("   1. https://github.com/settings/tokens/new")
        print("   2. Scope: public_repo (nur das!)")
        print("   3. Token kopieren")
        print("   4. In diesem Script eintragen: GITHUB_TOKEN = 'ghp_XXXXX'")
        print("   5. Script nochmal starten\n")
        return False
    
    print("🚀 Pushing files to GitHub...\n")
    
    success_count = 0
    for local_path, github_path in FILES_TO_PUSH:
        if os.path.exists(local_path):
            if push_file_to_github(local_path, github_path, GITHUB_TOKEN):
                success_count += 1
        else:
            print(f"⚠️  {local_path} nicht gefunden")
    
    print(f"\n✅ {success_count}/{len(FILES_TO_PUSH)} Dateien erfolgreich gepusht!")
    print(f"   https://github.com/{REPO}\n")
    
    return True

if __name__ == '__main__':
    main()
