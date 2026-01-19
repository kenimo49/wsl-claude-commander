# Move and resize a window by process ID or window title
# Usage: move-window.ps1 -ProcessId <pid> -X <x> -Y <y> -Width <w> -Height <h>
#        move-window.ps1 -Title <title> -X <x> -Y <y> -Width <w> -Height <h>

param(
    [Parameter(Mandatory=$false)]
    [int]$ProcessId,

    [Parameter(Mandatory=$false)]
    [string]$Title,

    [Parameter(Mandatory=$true)]
    [int]$X,

    [Parameter(Mandatory=$true)]
    [int]$Y,

    [Parameter(Mandatory=$true)]
    [int]$Width,

    [Parameter(Mandatory=$true)]
    [int]$Height
)

# Add Windows API functions
Add-Type @"
using System;
using System.Runtime.InteropServices;

public class WindowHelper {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public const uint SWP_NOZORDER = 0x0004;
    public const uint SWP_SHOWWINDOW = 0x0040;
    public const int SW_RESTORE = 9;
}
"@

function Get-WindowHandleByProcessId {
    param([int]$ProcessId)

    $hwnd = [IntPtr]::Zero
    $targetPid = [uint32]$ProcessId

    $callback = [WindowHelper+EnumWindowsProc]{
        param([IntPtr]$hWnd, [IntPtr]$lParam)

        $pid = [uint32]0
        [WindowHelper]::GetWindowThreadProcessId($hWnd, [ref]$pid) | Out-Null

        if ($pid -eq $targetPid -and [WindowHelper]::IsWindowVisible($hWnd)) {
            $script:hwnd = $hWnd
            return $false  # Stop enumeration
        }
        return $true  # Continue enumeration
    }

    [WindowHelper]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
    return $script:hwnd
}

function Get-WindowHandleByTitle {
    param([string]$Title)

    $hwnd = [IntPtr]::Zero

    $callback = [WindowHelper+EnumWindowsProc]{
        param([IntPtr]$hWnd, [IntPtr]$lParam)

        if ([WindowHelper]::IsWindowVisible($hWnd)) {
            $sb = New-Object System.Text.StringBuilder 256
            [WindowHelper]::GetWindowText($hWnd, $sb, $sb.Capacity) | Out-Null
            $windowTitle = $sb.ToString()

            if ($windowTitle -like "*$Title*") {
                $script:hwnd = $hWnd
                return $false  # Stop enumeration
            }
        }
        return $true  # Continue enumeration
    }

    [WindowHelper]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
    return $script:hwnd
}

# Find the window handle
$hwnd = [IntPtr]::Zero

if ($ProcessId -gt 0) {
    $hwnd = Get-WindowHandleByProcessId -ProcessId $ProcessId
} elseif ($Title) {
    $hwnd = Get-WindowHandleByTitle -Title $Title
} else {
    Write-Error "Either -ProcessId or -Title must be specified"
    exit 1
}

if ($hwnd -eq [IntPtr]::Zero) {
    Write-Error "Window not found"
    exit 1
}

# Restore window if minimized
[WindowHelper]::ShowWindow($hwnd, [WindowHelper]::SW_RESTORE) | Out-Null

# Move and resize the window
$result = [WindowHelper]::SetWindowPos(
    $hwnd,
    [IntPtr]::Zero,
    $X,
    $Y,
    $Width,
    $Height,
    [WindowHelper]::SWP_NOZORDER -bor [WindowHelper]::SWP_SHOWWINDOW
)

if ($result) {
    Write-Output "Window moved successfully"
    exit 0
} else {
    Write-Error "Failed to move window"
    exit 1
}
