use anyhow::Result;
use clap::{Parser, Subcommand};
use tracing::info;
use tracing_subscriber::EnvFilter;

mod config;

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
    Launch,

    /// Show current configuration
    Config,

    /// Validate configuration file
    Validate,
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
        Commands::Launch => {
            info!("Loading config from: {}", cli.config);
            let config = config::load(&cli.config)?;
            info!("Config loaded: {:?}", config);
            // TODO: Implement launch logic
            println!("Launch command - not yet implemented");
        }
        Commands::Config => {
            let config = config::load(&cli.config)?;
            println!("{:#?}", config);
        }
        Commands::Validate => {
            match config::load(&cli.config) {
                Ok(_) => println!("Configuration is valid!"),
                Err(e) => println!("Configuration error: {}", e),
            }
        }
    }

    Ok(())
}
