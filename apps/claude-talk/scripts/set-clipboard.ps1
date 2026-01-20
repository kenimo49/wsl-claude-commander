# Set clipboard text
# Usage: powershell.exe -File set-clipboard.ps1 -Text "hello world"

param(
    [string]$Text = ""
)

Add-Type -AssemblyName System.Windows.Forms

try {
    [System.Windows.Forms.Clipboard]::SetText($Text)
    @{ success = $true } | ConvertTo-Json
} catch {
    @{ success = $false; error = $_.Exception.Message } | ConvertTo-Json
    exit 1
}
