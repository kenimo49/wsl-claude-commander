use anyhow::{Context, Result};
use std::process::Command;
use tracing::{debug, info};

use crate::config::WindowConfig;

/// Launcher for WSL windows
pub struct WslLauncher {
    distribution: String,
}

impl WslLauncher {
    /// Create a new WSL launcher
    pub fn new(distribution: &str) -> Self {
        Self {
            distribution: distribution.to_string(),
        }
    }

    /// Launch a single WSL window using Windows Terminal
    pub fn launch_window(&self, window: &WindowConfig) -> Result<()> {
        info!("Launching window: {}", window.name);

        // Build the command to run inside WSL
        let wsl_command = self.build_wsl_command(window);
        debug!("WSL command: {}", wsl_command);

        // Use cmd.exe to start Windows Terminal with a new window
        // wt.exe -w new creates a new window
        let mut cmd = Command::new("cmd.exe");
        cmd.args([
            "/c",
            "start",
            "",  // Empty title
            "wt.exe",
            "-w", "new",  // New window
            "wsl.exe",
            "-d", &self.distribution,
            "--",
            "bash", "-c", &wsl_command,
        ]);

        debug!("Executing: {:?}", cmd);

        let status = cmd
            .status()
            .context("Failed to execute Windows Terminal")?;

        if !status.success() {
            anyhow::bail!("Windows Terminal exited with status: {}", status);
        }

        info!("Window '{}' launched successfully", window.name);
        Ok(())
    }

    /// Launch multiple windows with a delay between each
    pub fn launch_windows(&self, windows: &[WindowConfig]) -> Result<()> {
        for (i, window) in windows.iter().enumerate() {
            self.launch_window(window)?;

            // Add a small delay between window launches to prevent race conditions
            if i < windows.len() - 1 {
                std::thread::sleep(std::time::Duration::from_millis(500));
            }
        }
        Ok(())
    }

    /// Build the command to run inside WSL
    fn build_wsl_command(&self, window: &WindowConfig) -> String {
        let mut parts = Vec::new();

        // Change to working directory if specified
        if let Some(ref dir) = window.working_dir {
            // Expand ~ to $HOME
            let expanded = if dir.starts_with('~') {
                dir.replacen('~', "$HOME", 1)
            } else {
                dir.clone()
            };
            parts.push(format!("cd {}", expanded));
        }

        // Add the main command
        parts.push(window.command.clone());

        // Join with && to execute sequentially
        if parts.len() > 1 {
            parts.join(" && ")
        } else {
            parts.into_iter().next().unwrap_or_else(|| "bash".to_string())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_wsl_command_simple() {
        let launcher = WslLauncher::new("Ubuntu-24.04");
        let window = WindowConfig {
            name: "test".to_string(),
            command: "htop".to_string(),
            working_dir: None,
        };
        assert_eq!(launcher.build_wsl_command(&window), "htop");
    }

    #[test]
    fn test_build_wsl_command_with_dir() {
        let launcher = WslLauncher::new("Ubuntu-24.04");
        let window = WindowConfig {
            name: "test".to_string(),
            command: "claude".to_string(),
            working_dir: Some("~/workspace".to_string()),
        };
        assert_eq!(
            launcher.build_wsl_command(&window),
            "cd $HOME/workspace && claude"
        );
    }

    #[test]
    fn test_build_wsl_command_absolute_dir() {
        let launcher = WslLauncher::new("Ubuntu-24.04");
        let window = WindowConfig {
            name: "test".to_string(),
            command: "bash".to_string(),
            working_dir: Some("/tmp".to_string()),
        };
        assert_eq!(launcher.build_wsl_command(&window), "cd /tmp && bash");
    }
}
