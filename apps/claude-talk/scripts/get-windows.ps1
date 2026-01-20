param(
    [string]$TitlePattern = ""
)

# Set UTF-8 output encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public class WindowHelper {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public static List<Tuple<IntPtr, string>> Windows = new List<Tuple<IntPtr, string>>();

    public static bool EnumWindowCallback(IntPtr hWnd, IntPtr lParam) {
        if (!IsWindowVisible(hWnd)) return true;

        StringBuilder title = new StringBuilder(256);
        GetWindowText(hWnd, title, 256);
        string titleStr = title.ToString();

        if (!string.IsNullOrWhiteSpace(titleStr)) {
            Windows.Add(new Tuple<IntPtr, string>(hWnd, titleStr));
        }
        return true;
    }

    public static void GetAllWindows() {
        Windows.Clear();
        EnumWindows(EnumWindowCallback, IntPtr.Zero);
    }
}
"@

# Get all windows
[WindowHelper]::GetAllWindows()

# Get foreground window
$foreground = [WindowHelper]::GetForegroundWindow()

# Filter windows by pattern
$windows = @()
foreach ($win in [WindowHelper]::Windows) {
    $handle = $win.Item1.ToInt64()
    $title = $win.Item2

    if ([string]::IsNullOrEmpty($TitlePattern) -or $title -like "*$TitlePattern*") {
        $windows += @{
            handle = $handle
            title = $title
        }
    }
}

# Output JSON
$result = @{
    success = $true
    foreground = $foreground.ToInt64()
    windows = $windows
}

$result | ConvertTo-Json -Compress
