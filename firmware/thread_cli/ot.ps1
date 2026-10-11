# Sends OpenThread CLI commands to a board over a serial port and prints the replies.
# Example: .\ot.ps1 -Port COM15 -Commands 'ot state','ot ipaddr'
param(
    [Parameter(Mandatory)][string]$Port,
    [Parameter(Mandatory)][string[]]$Commands,
    [int]$WaitMs = 1500,
    [int]$Baud = 115200
)

$sp = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$sp.DtrEnable = $true
$sp.RtsEnable = $true
$sp.NewLine = "`r"
$sp.Open()
try {
    Start-Sleep -Milliseconds 300
    $sp.WriteLine('')
    Start-Sleep -Milliseconds 300
    $null = $sp.ReadExisting()

    foreach ($cmd in $Commands) {
        if ($cmd -match '^sleep (\d+)$') {
            Start-Sleep -Milliseconds ([int]$Matches[1])
            continue
        }
        $sp.WriteLine($cmd)
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $buf = ''
        while ($sw.ElapsedMilliseconds -lt $WaitMs) {
            $buf += $sp.ReadExisting()
            Start-Sleep -Milliseconds 50
        }
        # Strip ANSI colour codes that the Zephyr shell prints.
        $buf = $buf -replace "`e\[[0-9;]*[A-Za-z]", ''
        "> $cmd"
        $buf -split "`r?`n" | Where-Object { $_.Trim() -and $_.Trim() -ne $cmd -and $_ -notmatch '^\s*uart:~\$\s*$' } | ForEach-Object { "  " + $_.Trim() }
    }
} finally {
    $sp.Close()
}
