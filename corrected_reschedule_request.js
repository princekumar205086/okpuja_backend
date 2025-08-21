const axios = require('axios');

let data = JSON.stringify({
  "selected_date": "2025-08-27",
  "selected_time": "16:00:00",
  "reason": "Schedule change requested"
});

let config = {
  method: 'post',
  maxBodyLength: Infinity,
  url: 'https://api.okpuja.com/api/booking/admin/bookings/28/reschedule/',  // ✅ CORRECTED URL
  headers: { 
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU1NzgxNTg4LCJpYXQiOjE3NTU3NzQzODgsImp0aSI6ImNhMzg0ZWE1N2I3YTQyY2RiNDQ4NmRjNDA4OTczYWM1IiwidXNlcl9pZCI6MSwicm9sZSI6IkFETUlOIiwiYWNjb3VudF9zdGF0dXMiOiJBQ1RJVkUiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0.Ew6tKGGgXPaO0m_Ee9xogO3twlBaCJ_As-DvJeje5XE', 
    'Content-Type': 'application/json'
  },
  data : data
};

axios.request(config)
.then((response) => {
  console.log(JSON.stringify(response.data));
})
.catch((error) => {
  console.log(error);
});