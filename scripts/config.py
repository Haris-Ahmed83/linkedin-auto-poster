import os
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_REFRESH_TOKEN = os.getenv("LINKEDIN_REFRESH_TOKEN")
LINKEDIN_USER_URN = os.getenv("LINKEDIN_USER_URN")

GH_TOKEN = os.getenv("GH_TOKEN")
GH_USERNAME = "Haris-Ahmed83"

POSTING_DAYS = [0, 1, 2, 3, 4, 5]  # Mon=0 .. Sat=5 (skip Sunday=6)
POSTING_TIMES_PKT = {
    0: "08:30",  # Mon 8:30 AM PKT
    1: "08:30",  # Tue 8:30 AM PKT
    2: "15:00",  # Wed 3:00 PM PKT (UK + US reach)
    3: "08:30",  # Thu 8:30 AM PKT
    4: "08:30",  # Fri 8:30 AM PKT
    5: "10:00",  # Sat 10:00 AM PKT (weekend, later time)
}

COOLDOWN_DAYS = 7
DRY_RUN = False  # Live posting enabled
MAX_POST_LENGTH = 3000
MIN_POST_LENGTH = 1200
