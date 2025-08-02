import requests

response = requests.get('http://127.0.0.1:8000/api/payments/redirect/simple/', allow_redirects=False)
print(f'Status: {response.status_code}')
if 'Location' in response.headers:
    print(f'Redirect URL: {response.headers["Location"]}')
else:
    print('No redirect found')
    print(response.text)
