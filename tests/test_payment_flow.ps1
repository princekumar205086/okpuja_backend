#!/usr/bin/env pwsh
# PowerShell script to test payment flow
# Run with: powershell -ExecutionPolicy Bypass -File test_payment_flow.ps1

Write-Host "🧪 Payment Flow Test Script" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

$baseUrl = "http://localhost:8000"
$email = "asliprinceraj@gmail.com"
$password = "testpass123"

try {
    # Step 1: Login
    Write-Host "`n🔑 Step 1: User Authentication" -ForegroundColor Yellow
    $loginBody = @{
        email = $email
        password = $password
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/accounts/auth/login/" -Method POST -Body $loginBody -ContentType 'application/json' -TimeoutSec 10
    $token = $loginResponse.access
    
    if ($token) {
        Write-Host "   ✅ Login successful" -ForegroundColor Green
        Write-Host "   Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
    } else {
        throw "No access token received"
    }
    
    # Step 2: Get Puja Services
    Write-Host "`n📋 Step 2: Get Puja Services" -ForegroundColor Yellow
    $headers = @{
        'Authorization' = "Bearer $token"
        'Content-Type' = 'application/json'
    }
    
    $services = Invoke-RestMethod -Uri "$baseUrl/api/puja/services/" -Headers $headers -TimeoutSec 10
    
    if ($services -and $services.results -and $services.results.Count -gt 0) {
        $service = $services.results[0]
        $serviceId = $service.id
        $serviceName = $service.name
        
        Write-Host "   ✅ Found services: $($services.results.Count)" -ForegroundColor Green
        Write-Host "   Using: $serviceName (ID: $serviceId)" -ForegroundColor Gray
        
        if ($service.packages -and $service.packages.Count -gt 0) {
            $package = $service.packages[0]
            $packageId = $package.id
            $packageName = $package.name
            $packagePrice = $package.price
            
            Write-Host "   Package: $packageName (ID: $packageId) - ₹$packagePrice" -ForegroundColor Gray
        } else {
            throw "No packages found for service"
        }
    } else {
        throw "No puja services found"
    }
    
    # Step 3: Create Cart
    Write-Host "`n🛒 Step 3: Create Cart" -ForegroundColor Yellow
    $futureDate = (Get-Date).AddDays(7).ToString("yyyy-MM-dd")
    $cartBody = @{
        service_type = "PUJA"
        puja_service = $serviceId
        package = $packageId
        selected_date = $futureDate
        selected_time = "10:00"
    } | ConvertTo-Json
    
    $cart = Invoke-RestMethod -Uri "$baseUrl/api/cart/carts/" -Method POST -Body $cartBody -Headers $headers -TimeoutSec 10
    $cartId = $cart.id
    $totalPrice = $cart.total_price
    
    Write-Host "   ✅ Cart created: ID $cartId" -ForegroundColor Green
    Write-Host "   Total Price: ₹$totalPrice" -ForegroundColor Gray
    Write-Host "   Date: $futureDate, Time: 10:00" -ForegroundColor Gray
    
    # Step 4: Test PhonePe Connectivity
    Write-Host "`n🔍 Step 4: Test PhonePe Connectivity" -ForegroundColor Yellow
    try {
        $debugInfo = Invoke-RestMethod -Uri "$baseUrl/api/payments/payments/debug-connectivity/" -Headers $headers -TimeoutSec 10
        $phonepeReachable = $false
        
        foreach ($test in $debugInfo.network_tests.PSObject.Properties) {
            if ($test.Name -like "*phonepe.com*" -and $test.Value.reachable -eq $true) {
                $phonepeReachable = $true
                break
            }
        }
        
        if ($phonepeReachable) {
            Write-Host "   ✅ PhonePe API is reachable" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ PhonePe API connectivity issues detected" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️ Debug connectivity test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Step 5: Process Payment
    Write-Host "`n💳 Step 5: Process Payment" -ForegroundColor Yellow
    $paymentBody = @{
        cart_id = $cartId
        method = "PHONEPE"
    } | ConvertTo-Json
    
    try {
        $payment = Invoke-RestMethod -Uri "$baseUrl/api/payments/payments/process-cart/" -Method POST -Body $paymentBody -Headers $headers -TimeoutSec 30
        
        if ($payment.success) {
            Write-Host "   ✅ Payment processing successful!" -ForegroundColor Green
            Write-Host "   Payment ID: $($payment.payment_id)" -ForegroundColor Gray
            Write-Host "   Transaction ID: $($payment.transaction_id)" -ForegroundColor Gray
            Write-Host "   Amount: ₹$($payment.amount)" -ForegroundColor Gray
            
            if ($payment.payment_url) {
                Write-Host "   🔗 Payment URL: $($payment.payment_url)" -ForegroundColor Cyan
                Write-Host "`n   📋 Next Steps:" -ForegroundColor Yellow
                Write-Host "   1. Copy the payment URL above" -ForegroundColor Gray
                Write-Host "   2. Open it in your browser" -ForegroundColor Gray
                Write-Host "   3. Complete payment using PhonePe Test App" -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️ Payment initiation returned success=false" -ForegroundColor Yellow
        }
        
    } catch {
        $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        
        if ($errorResponse -and $errorResponse.debug_options -and $errorResponse.debug_options.simulate_payment_url) {
            Write-Host "   ⚠️ Payment gateway connectivity failed" -ForegroundColor Yellow
            Write-Host "   Error: $($errorResponse.user_message)" -ForegroundColor Red
            Write-Host "`n   🎯 Attempting payment simulation..." -ForegroundColor Yellow
            
            # Try payment simulation
            try {
                $simulateUrl = $errorResponse.debug_options.simulate_payment_url
                $simulation = Invoke-RestMethod -Uri "$baseUrl$simulateUrl" -Method POST -Headers $headers -TimeoutSec 10
                
                Write-Host "   ✅ Payment simulation successful!" -ForegroundColor Green
                Write-Host "   Payment ID: $($simulation.payment_id)" -ForegroundColor Gray
                Write-Host "   Status: $($simulation.status)" -ForegroundColor Gray
                
                if ($simulation.booking_created) {
                    Write-Host "   Booking Created: $($simulation.booking_id)" -ForegroundColor Green
                }
                
            } catch {
                Write-Host "   ❌ Payment simulation also failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "   ❌ Payment processing failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n" + "="*50 -ForegroundColor Green
    Write-Host "✅ Payment test completed!" -ForegroundColor Green
    Write-Host "`n📊 Test Summary:" -ForegroundColor Yellow
    Write-Host "   User: $email" -ForegroundColor Gray
    Write-Host "   Service: $serviceName (ID: $serviceId)" -ForegroundColor Gray
    Write-Host "   Package: $packageName (ID: $packageId)" -ForegroundColor Gray
    Write-Host "   Cart: ID $cartId - ₹$totalPrice" -ForegroundColor Gray
    Write-Host "   Server: localhost:8000" -ForegroundColor Gray
    
} catch {
    Write-Host "`n❌ Test failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n🔧 Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "   1. Ensure Django server is running on localhost:8000" -ForegroundColor Gray
    Write-Host "   2. Check if user exists with correct credentials" -ForegroundColor Gray
    Write-Host "   3. Verify puja services and packages exist in database" -ForegroundColor Gray
    Write-Host "   4. Check Django logs for detailed error information" -ForegroundColor Gray
}
