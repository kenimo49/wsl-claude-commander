# Send keyboard input to active window
# Usage: powershell.exe -File send-keys.ps1 -Keys "^v{ENTER}"
# Keys format: https://docs.microsoft.com/en-us/dotnet/api/system.windows.forms.sendkeys

param(
    [string]$Keys = ""
)

Add-Type -AssemblyName System.Windows.Forms

try {
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait($Keys)
    @{ success = $true } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
    exit 1
}
