# Prints everything a board sends on a serial port, until you press Ctrl+C.
# Example: .\monitor.ps1 -Port COM16
param(
    [Parameter(Mandatory)][string]$Port,
    [int]$Baud = 115200,
    [int]$Seconds = 0
)

$sp = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.Open()
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
    while ($Seconds -eq 0 -or $sw.Elapsed.TotalSeconds -lt $Seconds) {
        $text = $sp.ReadExisting()
        if ($text) {
            [Console]::Write($text)
        }
        Start-Sleep -Milliseconds 100
    }
} finally {
    $sp.Close()
}
