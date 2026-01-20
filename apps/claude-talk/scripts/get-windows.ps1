# Get windows matching a title pattern
# Usage: powershell.exe -File get-windows.ps1 -TitlePattern "claude"

param(
    [string]$TitlePattern = ""
)

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public class WindowHelper {
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll")]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public static List<object[]> GetWindows(string pattern) {
        var windows = new List<object[]>();

        EnumWindows((hWnd, lParam) => {
            if (!IsWindowVisible(hWnd)) return true;

            int length = GetWindowTextLength(hWnd);
            if (length == 0) return true;

            StringBuilder sb = new StringBuilder(length + 1);
            GetWindowText(hWnd, sb, sb.Capacity);
            string title = sb.ToString();

            if (string.IsNullOrEmpty(pattern) || title.ToLower().Contains(pattern.ToLower())) {
                windows.Add(new object[] { hWnd.ToInt64(), title });
            }

            return true;
        }, IntPtr.Zero);

        return windows;
    }

    public static long GetForegroundWindowHandle() {
        return GetForegroundWindow().ToInt64();
    }
}
"@

$windows = [WindowHelper]::GetWindows($TitlePattern)
$foreground = [WindowHelper]::GetForegroundWindowHandle()

$result = @{
    windows = @()
    foreground = $foreground
}

foreach ($win in $windows) {
    $result.windows += @{
        handle = $win[0]
        title = $win[1]
    }
}

$result | ConvertTo-Json -Depth 3
