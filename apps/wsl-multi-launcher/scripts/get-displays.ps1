# Get display information
# Returns JSON with display details

Add-Type -AssemblyName System.Windows.Forms

$displays = [System.Windows.Forms.Screen]::AllScreens | ForEach-Object {
    @{
        DeviceName = $_.DeviceName
        Primary = $_.Primary
        Bounds = @{
            X = $_.Bounds.X
            Y = $_.Bounds.Y
            Width = $_.Bounds.Width
            Height = $_.Bounds.Height
        }
        WorkingArea = @{
            X = $_.WorkingArea.X
            Y = $_.WorkingArea.Y
            Width = $_.WorkingArea.Width
            Height = $_.WorkingArea.Height
        }
    }
}

$displays | ConvertTo-Json -Depth 3
