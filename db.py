import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def save_article(article):

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/articles",
        headers=headers,
        json=article
    )

    print("Supabase status:", response.status_code)

    if response.status_code not in [200, 201]:
        print(response.text)