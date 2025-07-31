# PhonePe V2 Payment Integration Test Runner
# PowerShell script to run all payment tests

Write-Host "🚀 PhonePe V2 Payment Integration Test Runner" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Yellow

# Change to project directory
$projectPath = "C:\Users\Prince Raj\Desktop\nextjs project\okpuja_backend"
Set-Location $projectPath

Write-Host "📁 Working directory: $projectPath" -ForegroundColor Cyan

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to activate virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Check if Django server is running
Write-Host "🔍 Checking if Django server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Django server is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Django server is not running. Starting server..." -ForegroundColor Yellow
    
    # Start Django server in background
    Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver" -WindowStyle Minimized
    
    # Wait for server to start
    Write-Host "⏳ Waiting for server to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Django server started successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start Django server: $_" -ForegroundColor Red
        exit 1
    }
}

# Run migrations
Write-Host "🔄 Running database migrations..." -ForegroundColor Yellow
try {
    python manage.py makemigrations
    python manage.py migrate
    Write-Host "✅ Migrations completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Migration failed: $_" -ForegroundColor Red
}

# Create superuser if needed (non-interactive)
Write-Host "👤 Ensuring test user exists..." -ForegroundColor Yellow
try {
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='test@okpuja.com').exists():
    user = User.objects.create_user(
        email='test@okpuja.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        phone_number='9999999999',
        is_verified=True
    )
    print('Test user created successfully')
else:
    print('Test user already exists')
"
    Write-Host "✅ Test user ready" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not create test user: $_" -ForegroundColor Yellow
}

# Test 1: PhonePe V2 Integration Tests
Write-Host "`n🧪 Running PhonePe V2 Integration Tests..." -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Yellow

try {
    python tests\test_phonepe_v2_integration.py
    Write-Host "✅ Integration tests completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Integration tests failed: $_" -ForegroundColor Red
}

# Test 2: API Endpoint Tests
Write-Host "`n🌐 Running API Endpoint Tests..." -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Yellow

try {
    python tests\test_payment_api.py
    Write-Host "✅ API tests completed" -ForegroundColor Green
} catch {
    Write-Host "❌ API tests failed: $_" -ForegroundColor Red
}

# Test 3: Django Unit Tests
Write-Host "`n🔬 Running Django Unit Tests..." -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Yellow

try {
    python manage.py test payment --verbosity=2
    Write-Host "✅ Django unit tests completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Django unit tests failed: $_" -ForegroundColor Red
}

# Test 4: Manual API Tests with curl-like commands
Write-Host "`n📡 Testing API Endpoints with Direct Requests..." -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Yellow

# Test connectivity endpoint
Write-Host "🔗 Testing connectivity endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/payments/payments/test-connectivity/" -Method GET
    Write-Host "✅ Connectivity test successful" -ForegroundColor Green
    Write-Host "Results: $($response.connectivity_results.Count) endpoints tested" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Connectivity test failed: $_" -ForegroundColor Red
}

# Test webhook debug endpoint
Write-Host "🔔 Testing webhook debug endpoint..." -ForegroundColor Cyan
try {
    $webhookData = @{
        response = "eyJ0ZXN0IjogInRydWUifQ=="
        merchantTransactionId = "TEST123456"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/payments/webhook/debug/" -Method POST -Body $webhookData -ContentType "application/json"
    Write-Host "✅ Webhook debug test successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Webhook debug test failed: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n" + "=" * 50 -ForegroundColor Yellow
Write-Host "🎯 Test Suite Completed!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Yellow

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Check the test results above" -ForegroundColor White
Write-Host "2. If tests passed, try creating a real payment:" -ForegroundColor White
Write-Host "   - Visit: http://localhost:8000/api/docs/" -ForegroundColor Yellow
Write-Host "   - Use the payment creation endpoint" -ForegroundColor Yellow
Write-Host "3. Test with PhonePe sandbox credentials" -ForegroundColor White
Write-Host "4. Monitor logs for any issues" -ForegroundColor White

Write-Host "`n🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "- View logs: python manage.py shell" -ForegroundColor White
Write-Host "- Test specific endpoint: python tests\test_payment_api.py" -ForegroundColor White
Write-Host "- Check PhonePe connectivity: python tests\test_phonepe_v2_integration.py" -ForegroundColor White

Write-Host "`n✨ Happy Testing!" -ForegroundColor Green
