# Print what a board writes to its serial port. Runs until Ctrl+C unless -Seconds is given.
#   tools\serial-log.ps1 COM13            # DK judge log, until Ctrl+C
#   tools\serial-log.ps1 COM15 -Seconds 30
#   tools\serial-log.ps1 COM15 -Send "judge status"
param(
	[Parameter(Mandatory = $true)] [string] $Port,
	[int] $Seconds = 0,
	[string] $Send = ""
)

$p = New-Object System.IO.Ports.SerialPort $Port, 115200, 'None', 8, 'One'
$p.DtrEnable = $true
$p.RtsEnable = $true
$p.ReadTimeout = 200
$p.NewLine = "`r`n"
$p.Open()
try {
	if ($Send -ne "") {
		Start-Sleep -Milliseconds 300
		$p.WriteLine("")
		Start-Sleep -Milliseconds 200
		$p.WriteLine($Send)
	}
	$end = if ($Seconds -gt 0) { (Get-Date).AddSeconds($Seconds) } else { [DateTime]::MaxValue }
	while ((Get-Date) -lt $end) {
		try {
			$line = $p.ReadLine()
			if ($line.Trim() -ne "") { Write-Output $line.TrimEnd() }
		} catch [TimeoutException] {}
	}
} finally {
	$p.Close()
}
