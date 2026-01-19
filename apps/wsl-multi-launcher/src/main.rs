use anyhow::Result;
use clap::{Parser, Subcommand};
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
        Commands::Launch { no_arrange } => {
            info!("Loading config from: {}", cli.config);
            let config = config::load(&cli.config)?;
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
            let displays = windows::get_displays()?;
            let display_area = windows::get_display_working_area(&displays, config.target_display)?;
            info!(
                "Target display working area: ({}, {}) {}x{}",
                display_area.x, display_area.y, display_area.width, display_area.height
            );

            // Calculate grid positions
            let grid = layout::GridLayout::new(cols, rows, display_area);
            let positions = grid.calculate_all_positions(config.windows.len());

            // Launch windows
            let launcher = wsl::WslLauncher::new(&config.wsl_distribution);

            for (i, window) in config.windows.iter().enumerate() {
                launcher.launch_window(window)?;
                debug!("Window {} launched, position will be {:?}", window.name, positions[i]);

                // Small delay to let window initialize
                std::thread::sleep(std::time::Duration::from_millis(800));
            }

            // Arrange windows if not skipped
            if !no_arrange {
                info!("Arranging windows...");
                // Wait a bit more for all windows to fully initialize
                std::thread::sleep(std::time::Duration::from_secs(2));

                for (i, window) in config.windows.iter().enumerate() {
                    let pos = &positions[i];
                    info!(
                        "Arranging '{}' at ({}, {}) {}x{}",
                        window.name, pos.x, pos.y, pos.width, pos.height
                    );

                    // Try to find and move the window
                    // Use the window name or a portion of the command as search term
                    if let Err(e) = windows::move_window_with_retry(&window.name, pos, 3) {
                        warn!("Failed to arrange window '{}': {}", window.name, e);
                    }
                }
            }

            println!(
                "Successfully launched {} windows",
                config.windows.len()
            );
        }

        Commands::Config => {
            let config = config::load(&cli.config)?;
            println!("{:#?}", config);
        }

        Commands::Validate => {
            match config::load(&cli.config) {
                Ok(config) => {
                    let (cols, rows) = config.layout.parse_grid()?;
                    println!("Configuration is valid!");
                    println!("  Distribution: {}", config.wsl_distribution);
                    println!("  Target display: {}", config.target_display);
                    println!("  Grid: {}x{} ({} cells)", cols, rows, cols * rows);
                    println!("  Windows: {}", config.windows.len());
                }
                Err(e) => println!("Configuration error: {}", e),
            }
        }

        Commands::Displays => {
            info!("Getting display information...");
            let displays = windows::get_displays()?;

            println!("Found {} display(s):", displays.len());
            for (i, display) in displays.iter().enumerate() {
                println!();
                println!("Display {}{}:", i, if display.primary { " (Primary)" } else { "" });
                println!("  Device: {}", display.device_name);
                println!(
                    "  Bounds: ({}, {}) {}x{}",
                    display.bounds.x,
                    display.bounds.y,
                    display.bounds.width,
                    display.bounds.height
                );
                println!(
                    "  Working Area: ({}, {}) {}x{}",
                    display.working_area.x,
                    display.working_area.y,
                    display.working_area.width,
                    display.working_area.height
                );
            }
        }

        Commands::Arrange => {
            info!("Loading config from: {}", cli.config);
            let config = config::load(&cli.config)?;
            let (cols, rows) = config.layout.parse_grid()?;

            // Get display information
            let displays = windows::get_displays()?;
            let display_area = windows::get_display_working_area(&displays, config.target_display)?;

            // Calculate grid positions
            let grid = layout::GridLayout::new(cols, rows, display_area);
            let positions = grid.calculate_all_positions(config.windows.len());

            info!("Arranging {} windows...", config.windows.len());

            for (i, window) in config.windows.iter().enumerate() {
                let pos = &positions[i];
                info!(
                    "Arranging '{}' at ({}, {}) {}x{}",
                    window.name, pos.x, pos.y, pos.width, pos.height
                );

                if let Err(e) = windows::move_window_with_retry(&window.name, pos, 3) {
                    warn!("Failed to arrange window '{}': {}", window.name, e);
                }
            }

            println!("Window arrangement complete");
        }
    }

    Ok(())
}
