import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request

OTP_TTL_SECONDS = 300  # 5 minutes


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp(phone: str, code: str) -> bool:
    """Send OTP via Kavenegar Lookup API. Falls back to console log when KAVENEGAR_API_KEY is not set."""
    api_key = os.environ.get('KAVENEGAR_API_KEY', '')
    if not api_key:
        # Dev mode: print to console instead of sending real SMS
        print(f"[OTP dev] {phone}: {code}")
        return True

    template = os.environ.get('KAVENEGAR_TEMPLATE', 'fundzi-otp')
    url = f"https://api.kavenegar.com/v1/{api_key}/verify/lookup.json"
    params = urllib.parse.urlencode({
        'receptor': phone,
        'token': code,
        'template': template,
    }).encode()
    try:
        req = urllib.request.Request(url, data=params, method='POST')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get('return', {}).get('status') == 200
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return False
