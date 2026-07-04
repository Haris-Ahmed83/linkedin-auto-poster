import requests
import time

class LinkedInAPI:
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def get_user_urn(self):
        url = f"{self.BASE_URL}/userinfo"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        return f"urn:li:person:{data['sub']}"

    def create_post(self, author_urn, content_text):
        url = f"{self.BASE_URL}/ugcPosts"
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        if resp.status_code == 201:
            return resp.json()
        raise Exception(f"Post failed: {resp.status_code} {resp.text}")

    def refresh_token(self, client_id, client_secret):
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.access_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            tokens = resp.json()
            self.access_token = tokens["access_token"]
            return tokens
        raise Exception(f"Token refresh failed: {resp.status_code} {resp.text}")
