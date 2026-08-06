param(
    [Parameter(Mandatory = $true)]
    [string]$Port,
    [int]$BaudRate = 115200,
    [string]$Payload = "QUECTEL-HOST",
    [int]$WaitMs = 500
)

$ErrorActionPreference = "Stop"
$serial = [System.IO.Ports.SerialPort]::new($Port, $BaudRate, "None", 8, "One")
$serial.ReadTimeout = [Math]::Max($WaitMs, 100)
$serial.WriteTimeout = 1000
$serial.NewLine = "`n"

try {
    $serial.Open()
    $serial.DiscardInBuffer()
    $serial.Write($Payload)
    Start-Sleep -Milliseconds $WaitMs
    $received = $serial.ReadExisting()
    if ($received -eq $Payload) {
        Write-Output "[HOST_SERIAL][PASS] port=$Port baud=$BaudRate payload=$Payload"
        exit 0
    }
    Write-Output "[HOST_SERIAL][FAIL] port=$Port sent=$Payload received=$received"
    exit 1
}
finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}

