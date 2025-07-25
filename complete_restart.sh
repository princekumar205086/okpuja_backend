#!/bin/bash
echo "🔧 COMPLETING GUNICORN RESTART"
echo "==============================="

echo ""
echo "4️⃣ Verifying no gunicorn processes remain..."
echo "ps aux | grep gunicorn"
ps aux | grep gunicorn

echo ""
echo "5️⃣ Clearing Python cache completely..."
find . -name '*.pyc' -delete
find . -name '__pycache__' -type d -exec rm -rf {} +
find . -name '*.pyo' -delete

echo ""
echo "6️⃣ Checking views.py imports..."
echo "grep -n 'gateways_v2' payment/views.py"
grep -n 'gateways_v2' payment/views.py

echo ""
echo "7️⃣ Starting gunicorn service..."
sudo systemctl start gunicorn_api_okpuja
sleep 3

echo ""
echo "8️⃣ Checking service status..."
sudo systemctl status gunicorn_api_okpuja --no-pager

echo ""
echo "9️⃣ Verifying new gunicorn processes..."
echo "ps aux | grep gunicorn"
ps aux | grep gunicorn

echo ""
echo "🔟 Testing V2 gateway..."
python simple_v2_check.py

echo ""
echo "1️⃣1️⃣ Checking view methods..."
python check_view_methods.py

echo ""
echo "✅ RESTART COMPLETE!"
echo "Now test your payment endpoint with authentication"
