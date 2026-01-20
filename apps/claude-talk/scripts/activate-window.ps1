param(
    [int64]$Handle = 0,
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
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public const int SW_RESTORE = 9;

    public static IntPtr FindWindowByTitle(string pattern) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((hWnd, lParam) => {
            if (!IsWindowVisible(hWnd)) return true;

            StringBuilder title = new StringBuilder(256);
            GetWindowText(hWnd, title, 256);
            string titleStr = title.ToString();

            if (titleStr.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) >= 0) {
                found = hWnd;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static bool Activate(IntPtr hWnd) {
        if (hWnd == IntPtr.Zero) return false;

        if (IsIconic(hWnd)) {
            ShowWindow(hWnd, SW_RESTORE);
        }

        return SetForegroundWindow(hWnd);
    }
}
"@

$success = $false
$hWnd = [IntPtr]::Zero

if ($Handle -ne 0) {
    $hWnd = [IntPtr]$Handle
} elseif (-not [string]::IsNullOrEmpty($Title)) {
    $hWnd = [WindowActivator]::FindWindowByTitle($Title)
}

if ($hWnd -ne [IntPtr]::Zero) {
    $success = [WindowActivator]::Activate($hWnd)
}

$result = @{
    success = $success
    handle = $hWnd.ToInt64()
}

$result | ConvertTo-Json -Compress
