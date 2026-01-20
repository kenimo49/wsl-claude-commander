# Activate a window by handle or title
# Usage: powershell.exe -File activate-window.ps1 -Handle 12345
# Usage: powershell.exe -File activate-window.ps1 -Title "claude"

param(
    [long]$Handle = 0,
    [string]$Title = ""
)

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public class WindowActivator {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public const int SW_RESTORE = 9;
    public const int SW_SHOW = 5;

    public static IntPtr FindWindowByTitle(string pattern) {
        IntPtr found = IntPtr.Zero;

        EnumWindows((hWnd, lParam) => {
            if (!IsWindowVisible(hWnd)) return true;

            int length = GetWindowTextLength(hWnd);
            if (length == 0) return true;

            StringBuilder sb = new StringBuilder(length + 1);
            GetWindowText(hWnd, sb, sb.Capacity);
            string title = sb.ToString();

            if (title.ToLower().Contains(pattern.ToLower())) {
                found = hWnd;
                return false; // Stop enumeration
            }

            return true;
        }, IntPtr.Zero);

        return found;
    }

    public static bool ActivateWindow(IntPtr hWnd) {
        if (hWnd == IntPtr.Zero) return false;

        // Restore if minimized
        if (IsIconic(hWnd)) {
            ShowWindow(hWnd, SW_RESTORE);
        } else {
            ShowWindow(hWnd, SW_SHOW);
        }

        return SetForegroundWindow(hWnd);
    }
}
"@

$targetHandle = [IntPtr]::Zero

if ($Handle -ne 0) {
    $targetHandle = [IntPtr]$Handle
} elseif ($Title -ne "") {
    $targetHandle = [WindowActivator]::FindWindowByTitle($Title)
}

if ($targetHandle -eq [IntPtr]::Zero) {
    @{ success = $false; error = "Window not found" } | ConvertTo-Json
    exit 1
}

$result = [WindowActivator]::ActivateWindow($targetHandle)

@{
    success = $result
    handle = $targetHandle.ToInt64()
} | ConvertTo-Json
