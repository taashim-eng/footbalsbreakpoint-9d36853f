"""
github_device_auth.py - GitHub Device Authorization Flow for footbalsbreakpoint.

Requests a device code from GitHub, prints the user code, polls for the access token,
and automatically updates the Git remote URL to push changes.
"""

import time
import requests
import subprocess
import os

CLIENT_ID = "178ee8a4fd8c2369496e"  # GitHub CLI Client ID (publicly available)
SCOPES = "repo"

def run_flow():
    print("=== GITHUB DEVICE AUTHENTICATION FOR TAASHIM-ENG ===")
    print("Requesting device code from GitHub...")
    
    # 1. Request device code
    resp = requests.post(
        "https://github.com/login/device/code",
        data={"client_id": CLIENT_ID, "scope": SCOPES},
        headers={"Accept": "application/json"}
    )
    
    if resp.status_code != 200:
        print(f"Error requesting device code: {resp.text}")
        return
        
    data = resp.json()
    device_code = data.get("device_code")
    user_code = data.get("user_code")
    verification_uri = data.get("verification_uri")
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 900)
    
    print("\n" + "=" * 60)
    print("ACTION REQUIRED:")
    print(f"1. Open your web browser and go to: {verification_uri}")
    print(f"2. Enter the following code: {user_code}")
    print("=" * 60 + "\n")
    print(f"This code will expire in {expires_in // 60} minutes.")
    print("Waiting for browser authorization...")
    
    # 2. Poll for token
    token = None
    start_time = time.time()
    
    while time.time() - start_time < expires_in:
        time.sleep(interval)
        
        poll_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            },
            headers={"Accept": "application/json"}
        )
        
        poll_data = poll_resp.json()
        
        if "error" in poll_data:
            err = poll_data["error"]
            if err == "authorization_pending":
                continue
            elif err == "slow_down":
                interval += 5
                continue
            elif err == "expired_token":
                print("Authorization code expired. Please rerun this script.")
                return
            else:
                print(f"Authentication failed: {poll_data.get('error_description', err)}")
                return
        
        if "access_token" in poll_data:
            token = poll_data["access_token"]
            break
            
    if not token:
        print("Polling timed out. Please run the script again.")
        return
        
    print("\nAuthorization successful!")
    print("Updating Git remote URL to use the new token...")
    
    # Update git remote to use token
    repo_url = f"https://{token}@github.com/taashim-eng/footbalsbreakpoint.git"
    try:
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
        print("Git remote updated successfully.")
        
        print("Pushing committed changes to GitHub (main branch)...")
        res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if res.returncode == 0:
            print("=== SUCCESS: Pushed code to taashim-eng/footbalsbreakpoint ===")
            print(res.stdout)
        else:
            print(f"Failed to push: {res.stderr}")
            # Restore standard URL to avoid writing token to repository config
            subprocess.run(["git", "remote", "set-url", "origin", "https://github.com/taashim-eng/footbalsbreakpoint.git"])
            print("Restored original Git remote URL.")
    except Exception as e:
        print(f"Error configuring Git remote: {e}")

if __name__ == "__main__":
    run_flow()
