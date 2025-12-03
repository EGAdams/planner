# verify_services.ps1
# Verify that the required services are running

Write-Host "`n=== Service Verification ===" -ForegroundColor Cyan

# Check Letta process
Write-Host "`nChecking for Letta process..." -ForegroundColor Yellow
$lettaProcess = Get-Process | Where-Object { $_.ProcessName -like "*letta*" -or $_.ProcessName -like "*python*" }
if ($lettaProcess) {
    Write-Host "✓ Found running processes:" -ForegroundColor Green
    $lettaProcess | Format-Table -Property ProcessName, Id, StartTime
}
else {
    Write-Host "✗ No Letta process found" -ForegroundColor Red
}

# Check Letta port
Write-Host "`nChecking Letta port (8283)..." -ForegroundColor Yellow
$lettaPort = netstat -ano | findstr :8283
if ($lettaPort) {
    Write-Host "✓ Port 8283 is in use:" -ForegroundColor Green
    Write-Host $lettaPort
}
else {
    Write-Host "✗ Port 8283 is not listening" -ForegroundColor Red
}

# Test Letta API
Write-Host "`nTesting Letta API endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8283/v1/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Letta server is responding:" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)"
    Write-Host "  Response: $($response.Content)"
}
catch {
    Write-Host "✗ Letta server is not responding:" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)"
}

# Check log files
Write-Host "`nChecking log files..." -ForegroundColor Yellow
if (Test-Path "letta_server.log") {
    Write-Host "✓ letta_server.log exists:" -ForegroundColor Green
    Write-Host "  Last 5 lines:"
    Get-Content letta_server.log -Tail 5 | ForEach-Object { Write-Host "    $_" }
}
else {
    Write-Host "✗ letta_server.log not found" -ForegroundColor Red
}

if (Test-Path "letta_server_err.log") {
    $errorContent = Get-Content letta_server_err.log
    if ($errorContent) {
        Write-Host "⚠ letta_server_err.log has content:" -ForegroundColor Yellow
        Write-Host "  Last 5 lines:"
        $errorContent | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" }
    }
}

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
