# PowerShell script to deploy PhonePe fix to production server
# Run this from your local Windows machine in PowerShell

Write-Host "🚀 DEPLOYING PHONEPE FIX TO PRODUCTION" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

$serverUser = "root"
$serverHost = "srv882943"
$serverPath = "/opt/api.okpuja.com"

Write-Host "`n📤 Uploading fixed gateway file..." -ForegroundColor Yellow

# Upload the fixed gateway file
try {
    scp "payment\gateways.py" "${serverUser}@${serverHost}:${serverPath}/payment/"
    Write-Host "✅ Gateway file uploaded successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to upload gateway file: $_" -ForegroundColor Red
    exit 1
}

# Upload test scripts
Write-Host "`n📤 Uploading test scripts..." -ForegroundColor Yellow
try {
    scp "simple_phonepe_test.py" "${serverUser}@${serverHost}:${serverPath}/"
    scp "comprehensive_phonepe_test.py" "${serverUser}@${serverHost}:${serverPath}/"
    Write-Host "✅ Test scripts uploaded successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Warning: Failed to upload test scripts" -ForegroundColor Yellow
}

Write-Host "`n🔄 Now SSH to your server and run these commands:" -ForegroundColor Cyan
Write-Host "ssh ${serverUser}@${serverHost}" -ForegroundColor White
Write-Host "cd ${serverPath}" -ForegroundColor White
Write-Host "sudo systemctl restart gunicorn_api_okpuja" -ForegroundColor White
Write-Host "sudo systemctl restart nginx" -ForegroundColor White
Write-Host "python simple_phonepe_test.py" -ForegroundColor White

Write-Host "`n✅ Files uploaded! Now restart services on the server." -ForegroundColor Green
