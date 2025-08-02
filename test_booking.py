import requests
import json

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU0MDc0NjIwLCJpYXQiOjE3NTQwNzEwMjAsImp0aSI6IjFiYjA5NmYxM2VjMDQwZDJiMTQwN2ZiMGZjZjI4MzA5IiwidXNlcl9pZCI6Miwicm9sZSI6IlVTRVIiLCJhY2NvdW50X3N0YXR1cyI6IkFDVElWRSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfQ.IDCH_z8zUJhw2ycIa7mOVikUuTJXZ_19xEQoM5oZUzo'
}

url = 'http://127.0.0.1:8000/api/booking/bookings/by-cart/d8fd1469-432d-47ad-951a-699d508eb1ca/'
response = requests.get(url, headers=headers)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'Booking ID: {data["data"]["book_id"]}')
    print(f'Status: {data["data"]["status"]}')
    print(f'Amount: Rs.{data["data"]["total_amount"]}')
    print('SUCCESS: Booking found!')
else:
    print(f'Response: {response.text}')
