# PowerShell script to register UrbanTwin Traffic Collector as a persistent Windows Scheduled Task
# This ensures data collection continues automatically even across computer restarts.

$TaskName = "UrbanTwin_TrafficCollector"
$ScriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) "scripts\traffic_collector_daemon.py"
$PythonPath = (Get-Command python).Source

Write-Host "Registering Windows Scheduled Task '$TaskName'..."
Write-Host "Python: $PythonPath"
Write-Host "Script: $ScriptPath"

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "-u `"$ScriptPath`"" -WorkingDirectory (Split-Path -Parent $PSScriptRoot)
$Trigger = New-ScheduledTaskTrigger -AtLogon
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "UrbanTwin continuous traffic collection daemon" -Force

Write-Host "Successfully registered '$TaskName' to start automatically at logon!"
