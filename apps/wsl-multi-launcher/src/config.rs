use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

/// Main configuration structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// WSL distribution name (e.g., "Ubuntu-24.04")
    pub wsl_distribution: String,

    /// Target display index (0 = primary, 1 = secondary, etc.)
    #[serde(default)]
    pub target_display: u32,

    /// Layout configuration
    pub layout: LayoutConfig,

    /// Window configurations
    pub windows: Vec<WindowConfig>,
}

/// Layout configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LayoutConfig {
    /// Grid format (e.g., "2x4" for 2 columns, 4 rows)
    pub grid: String,
}

impl LayoutConfig {
    /// Parse grid string into (columns, rows)
    pub fn parse_grid(&self) -> Result<(u32, u32)> {
        let parts: Vec<&str> = self.grid.split('x').collect();
        if parts.len() != 2 {
            anyhow::bail!("Invalid grid format: {}. Expected format: 'COLSxROWS' (e.g., '2x4')", self.grid);
        }
        let cols: u32 = parts[0].parse().context("Invalid column count")?;
        let rows: u32 = parts[1].parse().context("Invalid row count")?;
        Ok((cols, rows))
    }
}

/// Individual window configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowConfig {
    /// Window name/identifier
    pub name: String,

    /// Command to execute in the window
    #[serde(default = "default_command")]
    pub command: String,

    /// Working directory (supports ~ for home)
    #[serde(default)]
    pub working_dir: Option<String>,
}

fn default_command() -> String {
    "bash".to_string()
}

/// Load configuration from a YAML file
pub fn load<P: AsRef<Path>>(path: P) -> Result<Config> {
    let path = path.as_ref();
    let content = fs::read_to_string(path)
        .with_context(|| format!("Failed to read config file: {}", path.display()))?;

    let config: Config = serde_yaml::from_str(&content)
        .with_context(|| format!("Failed to parse config file: {}", path.display()))?;

    // Validate configuration
    validate(&config)?;

    Ok(config)
}

/// Validate configuration
fn validate(config: &Config) -> Result<()> {
    // Check grid format
    let (cols, rows) = config.layout.parse_grid()?;
    let max_windows = cols * rows;

    if config.windows.is_empty() {
        anyhow::bail!("At least one window must be configured");
    }

    if config.windows.len() > max_windows as usize {
        anyhow::bail!(
            "Too many windows configured: {} windows for {}x{} grid (max: {})",
            config.windows.len(),
            cols,
            rows,
            max_windows
        );
    }

    // Check for duplicate names
    let mut names = std::collections::HashSet::new();
    for window in &config.windows {
        if !names.insert(&window.name) {
            anyhow::bail!("Duplicate window name: {}", window.name);
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_grid() {
        let layout = LayoutConfig { grid: "2x4".to_string() };
        assert_eq!(layout.parse_grid().unwrap(), (2, 4));

        let layout = LayoutConfig { grid: "3x3".to_string() };
        assert_eq!(layout.parse_grid().unwrap(), (3, 3));
    }

    #[test]
    fn test_parse_grid_invalid() {
        let layout = LayoutConfig { grid: "invalid".to_string() };
        assert!(layout.parse_grid().is_err());
    }
}
