# Makes a Windows shortcut (.lnk) that runs Sari Utang with pythonw.exe (no black window).
# Used by create-shortcuts.bat and install-autostart.bat.
param(
    [Parameter(Mandatory = $true)] [ValidateSet("Desktop", "Startup")] [string] $Folder,
    [Parameter(Mandatory = $true)] [string] $Name,
    [Parameter(Mandatory = $true)] [string] $Flags
)
$appDir = Split-Path -Parent $PSScriptRoot
$pythonw = Join-Path $appDir ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $pythonw)) {
    Write-Host "Run run.bat first to set up Sari Utang."
    exit 1
}
$path = Join-Path ([Environment]::GetFolderPath($Folder)) "$Name.lnk"
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($path)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '"' + (Join-Path $appDir "start.py") + '" ' + $Flags
$shortcut.WorkingDirectory = $appDir
$shortcut.IconLocation = Join-Path $appDir "sari_utang\static\icon.ico"
$shortcut.Description = "Sari Utang"
$shortcut.Save()
Write-Host "Created: $path"
