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

POSTING_DAYS = [1, 2, 3]  # Mon=0, Tue=1, Wed=2, Thu=3, Fri=4
POSTING_TIMES_PKT = {
    1: "08:30",  # Tue 8:30 AM PKT (local audience)
    2: "15:00",  # Wed 3:00 PM PKT (UK + US reach)
    3: "08:30",  # Thu 8:30 AM PKT (local audience)
}

COOLDOWN_DAYS = 7
DRY_RUN = True  # First week: creates issues instead of posting
MAX_POST_LENGTH = 3000
MIN_POST_LENGTH = 1200
