# Get all Windows Terminal window handles
# Returns JSON array of window handles

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public class WTWindowFinder {
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    public static List<IntPtr> GetWindowsTerminalHandles() {
        var handles = new List<IntPtr>();

        EnumWindows((hWnd, lParam) => {
            if (!IsWindowVisible(hWnd)) return true;

            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);

            try {
                var proc = System.Diagnostics.Process.GetProcessById((int)pid);
                if (proc.ProcessName == "WindowsTerminal") {
                    var className = new StringBuilder(256);
                    GetClassName(hWnd, className, className.Capacity);
                    // Windows Terminal main windows have class CASCADIA_HOSTING_WINDOW_CLASS
                    if (className.ToString().Contains("CASCADIA")) {
                        handles.Add(hWnd);
                    }
                }
            } catch { }

            return true;
        }, IntPtr.Zero);

        return handles;
    }
}
"@

$handles = [WTWindowFinder]::GetWindowsTerminalHandles()
$result = $handles | ForEach-Object { $_.ToInt64() }
$result | ConvertTo-Json -Compress
