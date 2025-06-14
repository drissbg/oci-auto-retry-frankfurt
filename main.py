import time
import os

ads = os.getenv("OCI_AVAILABILITY_DOMAINS", "AD-1,AD-2,AD-3").split(",")
delay = int(os.getenv("SLEEP_SECONDS", 60))

while True:
    for ad in ads:
        print(f"[INFO] Trying {ad}...")
        time.sleep(2)
    print(f"[WAIT] Sleeping {delay}s before next attempt...")
    time.sleep(delay)
