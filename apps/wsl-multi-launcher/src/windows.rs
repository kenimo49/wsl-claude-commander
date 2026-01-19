use anyhow::{Context, Result};
use std::path::Path;
use std::process::Command;
use tracing::{debug, info};

use crate::layout::{DisplayInfo, Rect};

/// Get the path to the scripts directory
fn get_scripts_dir() -> Result<std::path::PathBuf> {
    // Try to find scripts relative to the executable
    let exe_path = std::env::current_exe().context("Failed to get executable path")?;
    let exe_dir = exe_path.parent().context("Failed to get executable directory")?;

    // Check common locations
    let possible_paths = [
        exe_dir.join("scripts"),
        exe_dir.join("../scripts"),
        exe_dir.join("../../scripts"),
        std::path::PathBuf::from("scripts"),
        std::path::PathBuf::from("./scripts"),
    ];

    for path in &possible_paths {
        if path.exists() {
            return Ok(path.clone());
        }
    }

    // Fall back to current directory
    Ok(std::path::PathBuf::from("scripts"))
}

/// Convert WSL path to Windows path
fn wsl_to_windows_path(wsl_path: &Path) -> Result<String> {
    let output = Command::new("wslpath")
        .args(["-w", wsl_path.to_str().unwrap()])
        .output()
        .context("Failed to convert path")?;

    if !output.status.success() {
        anyhow::bail!("wslpath failed: {}", String::from_utf8_lossy(&output.stderr));
    }

    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

/// Get display information using PowerShell
pub fn get_displays() -> Result<Vec<DisplayInfo>> {
    let scripts_dir = get_scripts_dir()?;
    let script_path = scripts_dir.join("get-displays.ps1");

    // Convert to Windows path for PowerShell
    let win_script_path = wsl_to_windows_path(&script_path)?;

    debug!("Running get-displays.ps1 from: {}", win_script_path);

    let output = Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", &win_script_path,
        ])
        .output()
        .context("Failed to execute get-displays.ps1")?;

    if !output.status.success() {
        anyhow::bail!(
            "get-displays.ps1 failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    let json = String::from_utf8_lossy(&output.stdout);
    debug!("Display info JSON: {}", json);

    // Parse JSON - can be single object or array
    let displays: Vec<DisplayInfo> = if json.trim().starts_with('[') {
        serde_json::from_str(&json).context("Failed to parse display info JSON")?
    } else {
        // Single display
        let single: DisplayInfo =
            serde_json::from_str(&json).context("Failed to parse display info JSON")?;
        vec![single]
    };

    info!("Found {} display(s)", displays.len());
    Ok(displays)
}

/// Get the working area for a specific display
pub fn get_display_working_area(displays: &[DisplayInfo], display_index: u32) -> Result<Rect> {
    let display = displays
        .get(display_index as usize)
        .context(format!("Display {} not found", display_index))?;

    Ok(Rect::new(
        display.working_area.x,
        display.working_area.y,
        display.working_area.width,
        display.working_area.height,
    ))
}

/// Move a window to the specified position
pub fn move_window(title: &str, rect: &Rect) -> Result<()> {
    let scripts_dir = get_scripts_dir()?;
    let script_path = scripts_dir.join("move-window.ps1");
    let win_script_path = wsl_to_windows_path(&script_path)?;

    debug!(
        "Moving window '{}' to ({}, {}, {}x{})",
        title, rect.x, rect.y, rect.width, rect.height
    );

    let output = Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", &win_script_path,
            "-Title", title,
            "-X", &rect.x.to_string(),
            "-Y", &rect.y.to_string(),
            "-Width", &rect.width.to_string(),
            "-Height", &rect.height.to_string(),
        ])
        .output()
        .context("Failed to execute move-window.ps1")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        // Don't fail if window not found - it might not be ready yet
        if stderr.contains("Window not found") {
            debug!("Window '{}' not found yet, will retry", title);
            return Ok(());
        }
        anyhow::bail!("move-window.ps1 failed: {}", stderr);
    }

    info!("Window '{}' moved successfully", title);
    Ok(())
}

/// Move a window with retries (for windows that may not be ready yet)
pub fn move_window_with_retry(title: &str, rect: &Rect, max_retries: u32) -> Result<()> {
    for attempt in 0..max_retries {
        match move_window(title, rect) {
            Ok(()) => return Ok(()),
            Err(e) => {
                if attempt < max_retries - 1 {
                    debug!(
                        "Attempt {} failed for window '{}': {}, retrying...",
                        attempt + 1,
                        title,
                        e
                    );
                    std::thread::sleep(std::time::Duration::from_millis(500));
                } else {
                    return Err(e);
                }
            }
        }
    }
    Ok(())
}

/// Get all Windows Terminal window handles
pub fn get_wt_window_handles() -> Result<Vec<i64>> {
    let scripts_dir = get_scripts_dir()?;
    let script_path = scripts_dir.join("get-wt-windows.ps1");
    let win_script_path = wsl_to_windows_path(&script_path)?;

    let output = Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", &win_script_path,
        ])
        .output()
        .context("Failed to execute get-wt-windows.ps1")?;

    if !output.status.success() {
        anyhow::bail!(
            "get-wt-windows.ps1 failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    let json = String::from_utf8_lossy(&output.stdout);
    let json = json.trim();

    // Parse JSON - can be single number, array, or null
    if json.is_empty() || json == "null" {
        return Ok(vec![]);
    }

    let handles: Vec<i64> = if json.starts_with('[') {
        serde_json::from_str(json).unwrap_or_default()
    } else {
        // Single handle
        json.parse::<i64>().map(|h| vec![h]).unwrap_or_default()
    };

    Ok(handles)
}

/// Move a window by its handle
pub fn move_window_by_handle(handle: i64, rect: &Rect) -> Result<()> {
    let scripts_dir = get_scripts_dir()?;
    let script_path = scripts_dir.join("move-window.ps1");
    let win_script_path = wsl_to_windows_path(&script_path)?;

    debug!(
        "Moving window handle {} to ({}, {}, {}x{})",
        handle, rect.x, rect.y, rect.width, rect.height
    );

    let output = Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", &win_script_path,
            "-Handle", &handle.to_string(),
            "-X", &rect.x.to_string(),
            "-Y", &rect.y.to_string(),
            "-Width", &rect.width.to_string(),
            "-Height", &rect.height.to_string(),
        ])
        .output()
        .context("Failed to execute move-window.ps1")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("move-window.ps1 failed: {}", stderr);
    }

    info!("Window handle {} moved successfully", handle);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_scripts_dir() {
        // This test just ensures the function doesn't panic
        let _ = get_scripts_dir();
    }
}
