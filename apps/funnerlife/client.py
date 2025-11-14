import requests
import os
from django.conf import settings


class FunnerLifeAPIClient:
    BASE_URL = os.getenv("FUNNERLIFE_API_BASE")
    API_KEY = os.getenv("FUNNERLIFE_API_KEY")

    @classmethod
    def get_services(cls):
        url = f"{cls.BASE_URL}service"
        payload = {"api_key": cls.API_KEY}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") is True:
                return data["data"]
            else:
                print(f"FunnerLife API Error: {data.get('msg')}")
                return []
        except Exception as e:
             print(f"Error fetching services: {e}")
             return None


