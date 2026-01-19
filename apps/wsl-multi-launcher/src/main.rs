use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::path::Path;
use tracing::{debug, info, warn};
use tracing_subscriber::EnvFilter;

mod config;
mod layout;
mod windows;
mod wsl;

#[derive(Parser)]
#[command(name = "wsl-multi-launcher")]
#[command(about = "Launch multiple WSL windows with grid layout on specified display")]
#[command(version)]
#[command(after_help = "Examples:
  # Initialize a new config file
  wsl-multi-launcher init

  # Show available displays
  wsl-multi-launcher displays

  # Launch windows with config
  wsl-multi-launcher -c config.yaml launch

  # Validate configuration
  wsl-multi-launcher -c config.yaml validate
")]
struct Cli {
    /// Path to config file
    #[arg(short, long, default_value = "config.yaml")]
    config: String,

    /// Enable verbose logging
    #[arg(short, long)]
    verbose: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize a new configuration file
    Init {
        /// Number of windows to configure
        #[arg(short, long, default_value = "4")]
        windows: u32,

        /// Grid layout (e.g., "2x2", "2x4")
        #[arg(short, long, default_value = "2x2")]
        grid: String,

        /// Target display index
        #[arg(short, long, default_value = "0")]
        display: u32,

        /// Force overwrite existing config
        #[arg(short, long)]
        force: bool,
    },

    /// Launch all configured windows
    Launch {
        /// Skip window arrangement (just launch)
        #[arg(long)]
        no_arrange: bool,
    },

    /// Show current configuration
    Config,

    /// Validate configuration file
    Validate,

    /// Show display information
    Displays,

    /// Arrange existing windows (without launching new ones)
    Arrange,

    /// Show system status and available WSL distributions
    Status,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    // Initialize logging
    let filter = if cli.verbose {
        EnvFilter::new("debug")
    } else {
        EnvFilter::new("info")
    };
    tracing_subscriber::fmt().with_env_filter(filter).init();

    info!("wsl-multi-launcher v{}", env!("CARGO_PKG_VERSION"));

    match cli.command {
        Commands::Init { windows: num_windows, grid, display, force } => {
            let config_path = Path::new(&cli.config);

            if config_path.exists() && !force {
                anyhow::bail!(
                    "Config file '{}' already exists. Use --force to overwrite.",
                    cli.config
                );
            }

            // Get available WSL distributions
            let distros = get_wsl_distributions()?;
            let default_distro = distros.first()
                .map(|s| s.as_str())
                .unwrap_or("Ubuntu-24.04");

            // Generate config content
            let config_content = generate_config(&grid, display, num_windows, default_distro)?;

            std::fs::write(config_path, &config_content)
                .with_context(|| format!("Failed to write config file: {}", cli.config))?;

            println!("Created config file: {}", cli.config);
            println!();
            println!("Next steps:");
            println!("  1. Edit {} to customize your windows", cli.config);
            println!("  2. Run 'wsl-multi-launcher displays' to see available displays");
            println!("  3. Run 'wsl-multi-launcher validate' to check your config");
            println!("  4. Run 'wsl-multi-launcher launch' to start!");
        }

        Commands::Launch { no_arrange } => {
            let config = load_config_with_helpful_error(&cli.config)?;
            let (cols, rows) = config.layout.parse_grid()?;

            info!(
                "Launching {} windows in {}x{} grid on display {} using {}",
                config.windows.len(),
                cols,
                rows,
                config.target_display,
                config.wsl_distribution
            );

            // Get display information
            let displays = windows::get_displays()
                .context("Failed to get display information. Make sure PowerShell is accessible.")?;

            let display_area = windows::get_display_working_area(&displays, config.target_display)
                .with_context(|| format!(
                    "Display {} not found. Run 'wsl-multi-launcher displays' to see available displays.",
                    config.target_display
                ))?;

            info!(
                "Target display working area: ({}, {}) {}x{}",
                display_area.x, display_area.y, display_area.width, display_area.height
            );

            // Calculate grid positions
            let grid = layout::GridLayout::new(cols, rows, display_area);
            let positions = grid.calculate_all_positions(config.windows.len());

            // Launch windows
            let launcher = wsl::WslLauncher::new(&config.wsl_distribution);

            println!("Launching {} windows...", config.windows.len());

            for (i, window) in config.windows.iter().enumerate() {
                print!("  [{}] {} ... ", i + 1, window.name);
                match launcher.launch_window(window) {
                    Ok(()) => println!("OK"),
                    Err(e) => {
                        println!("FAILED");
                        warn!("Failed to launch '{}': {}", window.name, e);
                    }
                }
                debug!("Window {} launched, position will be {:?}", window.name, positions[i]);

                // Small delay to let window initialize
                std::thread::sleep(std::time::Duration::from_millis(800));
            }

            // Arrange windows if not skipped
            if !no_arrange {
                println!();
                println!("Arranging windows...");
                // Wait a bit more for all windows to fully initialize
                std::thread::sleep(std::time::Duration::from_secs(2));

                for (i, window) in config.windows.iter().enumerate() {
                    let pos = &positions[i];
                    print!("  [{}] {} ... ", i + 1, window.name);

                    match windows::move_window_with_retry(&window.name, pos, 3) {
                        Ok(()) => println!("OK"),
                        Err(e) => {
                            println!("FAILED");
                            warn!("Failed to arrange '{}': {}", window.name, e);
                        }
                    }
                }
            }

            println!();
            println!("Done! {} windows launched.", config.windows.len());
        }

        Commands::Config => {
            let config = load_config_with_helpful_error(&cli.config)?;
            println!("{:#?}", config);
        }

        Commands::Validate => {
            match config::load(&cli.config) {
                Ok(config) => {
                    let (cols, rows) = config.layout.parse_grid()?;
                    println!("Configuration is valid!");
                    println!();
                    println!("  Distribution:   {}", config.wsl_distribution);
                    println!("  Target display: {}", config.target_display);
                    println!("  Grid:           {}x{} ({} cells)", cols, rows, cols * rows);
                    println!("  Windows:        {}", config.windows.len());
                    println!();
                    println!("Windows:");
                    for (i, w) in config.windows.iter().enumerate() {
                        println!("  {}. {} - '{}'", i + 1, w.name, w.command);
                        if let Some(ref dir) = w.working_dir {
                            println!("     working_dir: {}", dir);
                        }
                    }
                }
                Err(e) => {
                    println!("Configuration error!");
                    println!();
                    println!("{}", e);
                    println!();
                    println!("Hint: Run 'wsl-multi-launcher init' to create a new config file.");
                    std::process::exit(1);
                }
            }
        }

        Commands::Displays => {
            let displays = windows::get_displays()
                .context("Failed to get display information")?;

            println!("Found {} display(s):", displays.len());
            for (i, display) in displays.iter().enumerate() {
                println!();
                println!(
                    "  Display {} {}",
                    i,
                    if display.primary { "(Primary)" } else { "" }
                );
                println!("    Device:       {}", display.device_name);
                println!(
                    "    Resolution:   {}x{}",
                    display.bounds.width, display.bounds.height
                );
                println!(
                    "    Position:     ({}, {})",
                    display.bounds.x, display.bounds.y
                );
                println!(
                    "    Working Area: {}x{} at ({}, {})",
                    display.working_area.width,
                    display.working_area.height,
                    display.working_area.x,
                    display.working_area.y
                );
            }
            println!();
            println!("Use 'target_display: <index>' in your config to select a display.");
        }

        Commands::Arrange => {
            let config = load_config_with_helpful_error(&cli.config)?;
            let (cols, rows) = config.layout.parse_grid()?;

            let displays = windows::get_displays()?;
            let display_area = windows::get_display_working_area(&displays, config.target_display)?;

            let grid = layout::GridLayout::new(cols, rows, display_area);
            let positions = grid.calculate_all_positions(config.windows.len());

            println!("Arranging {} windows...", config.windows.len());

            for (i, window) in config.windows.iter().enumerate() {
                let pos = &positions[i];
                print!("  [{}] {} ... ", i + 1, window.name);

                match windows::move_window_with_retry(&window.name, pos, 3) {
                    Ok(()) => println!("OK"),
                    Err(e) => {
                        println!("FAILED");
                        warn!("Failed to arrange '{}': {}", window.name, e);
                    }
                }
            }

            println!();
            println!("Window arrangement complete.");
        }

        Commands::Status => {
            println!("System Status");
            println!("=============");
            println!();

            // WSL distributions
            println!("WSL Distributions:");
            match get_wsl_distributions() {
                Ok(distros) => {
                    if distros.is_empty() {
                        println!("  (none found)");
                    } else {
                        for distro in &distros {
                            println!("  - {}", distro);
                        }
                    }
                }
                Err(e) => println!("  Error: {}", e),
            }
            println!();

            // Displays
            println!("Displays:");
            match windows::get_displays() {
                Ok(displays) => {
                    for (i, d) in displays.iter().enumerate() {
                        println!(
                            "  {}. {} {}x{}{}",
                            i,
                            d.device_name,
                            d.bounds.width,
                            d.bounds.height,
                            if d.primary { " (Primary)" } else { "" }
                        );
                    }
                }
                Err(e) => println!("  Error: {}", e),
            }
            println!();

            // Config file
            println!("Config File:");
            let config_path = Path::new(&cli.config);
            if config_path.exists() {
                println!("  {} (exists)", cli.config);
                match config::load(&cli.config) {
                    Ok(c) => {
                        println!("  {} windows configured", c.windows.len());
                    }
                    Err(e) => {
                        println!("  Error: {}", e);
                    }
                }
            } else {
                println!("  {} (not found)", cli.config);
                println!("  Run 'wsl-multi-launcher init' to create one.");
            }
        }
    }

    Ok(())
}

/// Load config with helpful error messages
fn load_config_with_helpful_error(path: &str) -> Result<config::Config> {
    if !Path::new(path).exists() {
        anyhow::bail!(
            "Config file '{}' not found.\n\n\
            Hint: Run 'wsl-multi-launcher init' to create a new config file,\n\
            or use '-c <path>' to specify a different config file.",
            path
        );
    }
    config::load(path)
}

/// Get list of available WSL distributions
fn get_wsl_distributions() -> Result<Vec<String>> {
    let output = std::process::Command::new("wsl.exe")
        .args(["-l", "-q"])
        .output()
        .context("Failed to run wsl.exe")?;

    if !output.status.success() {
        anyhow::bail!("wsl.exe failed");
    }

    // Parse output (UTF-16 LE encoded on Windows)
    let stdout = String::from_utf8_lossy(&output.stdout);
    let distros: Vec<String> = stdout
        .lines()
        .map(|s| s.trim().replace('\0', ""))
        .filter(|s| !s.is_empty())
        .collect();

    Ok(distros)
}

/// Generate a default config file content
fn generate_config(grid: &str, display: u32, num_windows: u32, distro: &str) -> Result<String> {
    let parts: Vec<&str> = grid.split('x').collect();
    if parts.len() != 2 {
        anyhow::bail!("Invalid grid format. Use format like '2x2' or '2x4'.");
    }

    let mut windows_yaml = String::new();
    for i in 1..=num_windows {
        windows_yaml.push_str(&format!(
            r#"  - name: "window-{}"
    command: "bash"
    working_dir: "~"
"#,
            i
        ));
        if i < num_windows {
            windows_yaml.push('\n');
        }
    }

    Ok(format!(
        r#"# wsl-multi-launcher configuration
# Generated by 'wsl-multi-launcher init'

# WSL distribution name (run 'wsl -l -v' to see available distributions)
wsl_distribution: {}

# Target display index (run 'wsl-multi-launcher displays' to see available displays)
# 0 = primary display, 1 = secondary, etc.
target_display: {}

# Layout configuration
layout:
  # Grid format: "COLSxROWS"
  # Examples: "2x2" (4 windows), "2x4" (8 windows), "3x3" (9 windows)
  grid: "{}"

# Window configurations
# Each window will be placed in the grid from left to right, top to bottom
windows:
{}
"#,
        distro, display, grid, windows_yaml
    ))
}
