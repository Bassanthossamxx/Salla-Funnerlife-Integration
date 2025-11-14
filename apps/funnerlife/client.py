import requests
import os
from django.conf import settings
import uuid
import requests
from .services import build_target
from apps.salla.services import extract_player_id


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

def charge_funnerlife(item, funner_service):
    player_id = extract_player_id(item)
    zone_id = extract_zone_id(item)

    target = build_target(player_id, zone_id)

    service_id = item["sku"]
    kontak = settings.ADMIN_KONTAK
    idtrx = str(uuid.uuid4())

    payload = {
        "api_key": settings.FUNNERLIFE_API_KEY,
        "service_id": service_id,
        "target": target,
        "kontak": kontak,
        "idtrx": idtrx,
        "callback": settings.FUNNERLIFE_CALLBACK_URL,
    }

    response = requests.post("https://api.funnerlife.id/order", data=payload, timeout=20)

    try:
        resp_json = response.json()
    except:
        resp_json = {"raw": response.text}

    return {
        "idtrx": idtrx,
        "request_payload": payload,
        "response_payload": resp_json,
        "http_status": response.status_code,
    }
