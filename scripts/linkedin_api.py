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

    def register_image_upload(self, author_urn):
        url = f"{self.BASE_URL}/assets?action=registerUpload"
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()["value"]
            upload_url = data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset_urn = data["asset"]
            return upload_url, asset_urn
        raise Exception(f"Register image upload failed: {resp.status_code} {resp.text}")

    def upload_image_bytes(self, upload_url, image_bytes):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "image/jpeg"
        }
        resp = requests.put(upload_url, headers=headers, data=image_bytes)
        if resp.status_code in [200, 201]:
            return True
        raise Exception(f"Image upload failed: {resp.status_code} {resp.text}")

    def upload_image_asset(self, author_urn, image_bytes):
        upload_url, asset_urn = self.register_image_upload(author_urn)
        self.upload_image_bytes(upload_url, image_bytes)
        return asset_urn

    def create_post(self, author_urn, content_text, image_urn=None):
        url = f"{self.BASE_URL}/ugcPosts"
        
        if image_urn:
            share_content = {
                "shareCommentary": {
                    "text": content_text
                },
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Visual Content"
                        },
                        "media": image_urn,
                        "title": {
                            "text": "Visual"
                        }
                    }
                ]
            }
        else:
            share_content = {
                "shareCommentary": {
                    "text": content_text
                },
                "shareMediaCategory": "NONE"
            }

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
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
