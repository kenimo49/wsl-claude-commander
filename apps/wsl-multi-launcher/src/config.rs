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

        let layout = LayoutConfig { grid: "1x1".to_string() };
        assert_eq!(layout.parse_grid().unwrap(), (1, 1));
    }

    #[test]
    fn test_parse_grid_invalid() {
        let layout = LayoutConfig { grid: "invalid".to_string() };
        assert!(layout.parse_grid().is_err());

        let layout = LayoutConfig { grid: "2".to_string() };
        assert!(layout.parse_grid().is_err());

        let layout = LayoutConfig { grid: "axb".to_string() };
        assert!(layout.parse_grid().is_err());
    }

    #[test]
    fn test_parse_yaml_config() {
        let yaml = r#"
wsl_distribution: Ubuntu-24.04
target_display: 1
layout:
  grid: "2x2"
windows:
  - name: "test-1"
    command: "bash"
    working_dir: "~"
  - name: "test-2"
    command: "htop"
"#;
        let config: Config = serde_yaml::from_str(yaml).unwrap();
        assert_eq!(config.wsl_distribution, "Ubuntu-24.04");
        assert_eq!(config.target_display, 1);
        assert_eq!(config.layout.grid, "2x2");
        assert_eq!(config.windows.len(), 2);
        assert_eq!(config.windows[0].name, "test-1");
        assert_eq!(config.windows[0].command, "bash");
        assert_eq!(config.windows[0].working_dir, Some("~".to_string()));
        assert_eq!(config.windows[1].name, "test-2");
        assert_eq!(config.windows[1].command, "htop");
        assert_eq!(config.windows[1].working_dir, None);
    }

    #[test]
    fn test_default_command() {
        let yaml = r#"
wsl_distribution: Ubuntu
layout:
  grid: "1x1"
windows:
  - name: "test"
"#;
        let config: Config = serde_yaml::from_str(yaml).unwrap();
        assert_eq!(config.windows[0].command, "bash");
    }

    #[test]
    fn test_default_target_display() {
        let yaml = r#"
wsl_distribution: Ubuntu
layout:
  grid: "1x1"
windows:
  - name: "test"
"#;
        let config: Config = serde_yaml::from_str(yaml).unwrap();
        assert_eq!(config.target_display, 0);
    }

    #[test]
    fn test_validate_empty_windows() {
        let config = Config {
            wsl_distribution: "Ubuntu".to_string(),
            target_display: 0,
            layout: LayoutConfig { grid: "2x2".to_string() },
            windows: vec![],
        };
        assert!(validate(&config).is_err());
    }

    #[test]
    fn test_validate_too_many_windows() {
        let config = Config {
            wsl_distribution: "Ubuntu".to_string(),
            target_display: 0,
            layout: LayoutConfig { grid: "1x1".to_string() },
            windows: vec![
                WindowConfig { name: "a".to_string(), command: "bash".to_string(), working_dir: None },
                WindowConfig { name: "b".to_string(), command: "bash".to_string(), working_dir: None },
            ],
        };
        assert!(validate(&config).is_err());
    }

    #[test]
    fn test_validate_duplicate_names() {
        let config = Config {
            wsl_distribution: "Ubuntu".to_string(),
            target_display: 0,
            layout: LayoutConfig { grid: "2x2".to_string() },
            windows: vec![
                WindowConfig { name: "same".to_string(), command: "bash".to_string(), working_dir: None },
                WindowConfig { name: "same".to_string(), command: "bash".to_string(), working_dir: None },
            ],
        };
        assert!(validate(&config).is_err());
    }

    #[test]
    fn test_validate_success() {
        let config = Config {
            wsl_distribution: "Ubuntu".to_string(),
            target_display: 0,
            layout: LayoutConfig { grid: "2x2".to_string() },
            windows: vec![
                WindowConfig { name: "a".to_string(), command: "bash".to_string(), working_dir: None },
                WindowConfig { name: "b".to_string(), command: "bash".to_string(), working_dir: None },
            ],
        };
        assert!(validate(&config).is_ok());
    }
}
