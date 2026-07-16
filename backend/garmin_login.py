#!/usr/bin/env python3
"""Garmin login — מבקש אימייל+סיסמה בלי להדפיס, שומר tokens/"""
import os, sys, getpass
from dotenv import load_dotenv

load_dotenv(override=True)

email = input("Garmin email: ").strip()
password = getpass.getpass("Garmin password (hidden): ")

if not email or not password:
    print("Missing credentials")
    sys.exit(1)

# Save to .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
existing = ""
if os.path.exists(env_path):
    with open(env_path) as f:
        existing = f.read()

# Remove old garmin lines
lines = [l for l in existing.splitlines() if not l.startswith("GARMIN_")]
lines.append(f"GARMIN_EMAIL={email}")
lines.append(f"GARMIN_PASSWORD={password}")

with open(env_path, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"\n✅ Credentials saved to {env_path}")

# Try login + save tokens
try:
    from garminconnect import Garmin
    TOKEN_DIR = os.path.join(os.path.dirname(__file__), "tokens")
    os.makedirs(TOKEN_DIR, exist_ok=True)
    
    client = Garmin(email, password)
    client.login()
    client.garth.dump(TOKEN_DIR)
    print(f"✅ Garmin login OK — tokens saved to {TOKEN_DIR}")
    
    # Test: get last activity
    activities = client.get_activities(0, 1)
    if activities:
        act = activities[0]
        print(f"✅ Last activity: {act.get('activityName')} {act.get('startTimeLocal','')}")
except Exception as e:
    print(f"❌ Login failed: {e}")
    print("Credentials saved to .env — you can retry later with: python garmin_sync.py")