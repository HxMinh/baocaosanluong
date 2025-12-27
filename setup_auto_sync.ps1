$WshShell = New-Object -comObject WScript.Shell
$StartupDir = $WshShell.SpecialFolders.Item("Startup")
$TargetFile = "$PSScriptRoot\run_khsx_sync.bat"
$ShortcutFile = "$StartupDir\KHSX_Sync_Auto.lnk"

if (Test-Path $TargetFile) {
    $Shortcut = $WshShell.CreateShortcut($ShortcutFile)
    $Shortcut.TargetPath = $TargetFile
    $Shortcut.WorkingDirectory = $PSScriptRoot
    $Shortcut.Description = "Auto-sync KHSX on Startup"
    $Shortcut.Save()
    Write-Host "Success: Shortcut created at $ShortcutFile"
    Write-Host "The sync script will now run automatically when this computer starts."
} else {
    Write-Error "Error: Could not find run_khsx_sync.bat in the current directory."
}
