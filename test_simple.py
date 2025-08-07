import requests

def test_simple_endpoints():
    """Simple test of key endpoints"""
    print("Testing admin endpoints...")
    
    # Test without auth first
    endpoints = [
        'http://127.0.0.1:8000/api/astrology/admin/dashboard/',
        'http://127.0.0.1:8000/api/puja/admin/dashboard/',
        'http://127.0.0.1:8000/api/booking/admin/dashboard/'
    ]
    
    for url in endpoints:
        try:
            resp = requests.get(url, timeout=3)
            print(f"{url}: {resp.status_code}")
        except Exception as e:
            print(f"{url}: ERROR - {e}")

if __name__ == "__main__":
    test_simple_endpoints()
