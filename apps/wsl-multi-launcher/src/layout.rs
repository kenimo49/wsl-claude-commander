use serde::{Deserialize, Serialize};

/// Rectangle representing position and size
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Rect {
    pub x: i32,
    pub y: i32,
    pub width: i32,
    pub height: i32,
}

impl Rect {
    pub fn new(x: i32, y: i32, width: i32, height: i32) -> Self {
        Self { x, y, width, height }
    }
}

/// Display information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplayInfo {
    #[serde(rename = "DeviceName")]
    pub device_name: String,

    #[serde(rename = "Primary")]
    pub primary: bool,

    #[serde(rename = "Bounds")]
    pub bounds: BoundsInfo,

    #[serde(rename = "WorkingArea")]
    pub working_area: BoundsInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundsInfo {
    #[serde(rename = "X")]
    pub x: i32,

    #[serde(rename = "Y")]
    pub y: i32,

    #[serde(rename = "Width")]
    pub width: i32,

    #[serde(rename = "Height")]
    pub height: i32,
}

/// Grid layout calculator
pub struct GridLayout {
    cols: u32,
    rows: u32,
    display_area: Rect,
}

impl GridLayout {
    /// Create a new grid layout for the given display area
    pub fn new(cols: u32, rows: u32, display_area: Rect) -> Self {
        Self {
            cols,
            rows,
            display_area,
        }
    }

    /// Calculate the rectangle for a window at the given grid position
    /// Position is 0-indexed, starting from top-left
    pub fn calculate_position(&self, index: usize) -> Rect {
        let col = (index as u32) % self.cols;
        let row = (index as u32) / self.cols;

        let cell_width = self.display_area.width / self.cols as i32;
        let cell_height = self.display_area.height / self.rows as i32;

        Rect {
            x: self.display_area.x + (col as i32 * cell_width),
            y: self.display_area.y + (row as i32 * cell_height),
            width: cell_width,
            height: cell_height,
        }
    }

    /// Calculate positions for all windows
    pub fn calculate_all_positions(&self, count: usize) -> Vec<Rect> {
        (0..count).map(|i| self.calculate_position(i)).collect()
    }

    /// Get the maximum number of windows this grid can hold
    pub fn max_windows(&self) -> u32 {
        self.cols * self.rows
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_grid_layout_2x2() {
        let display = Rect::new(0, 0, 1920, 1080);
        let layout = GridLayout::new(2, 2, display);

        assert_eq!(layout.max_windows(), 4);

        // Top-left
        assert_eq!(layout.calculate_position(0), Rect::new(0, 0, 960, 540));
        // Top-right
        assert_eq!(layout.calculate_position(1), Rect::new(960, 0, 960, 540));
        // Bottom-left
        assert_eq!(layout.calculate_position(2), Rect::new(0, 540, 960, 540));
        // Bottom-right
        assert_eq!(layout.calculate_position(3), Rect::new(960, 540, 960, 540));
    }

    #[test]
    fn test_grid_layout_2x4() {
        let display = Rect::new(0, 0, 1920, 1080);
        let layout = GridLayout::new(2, 4, display);

        assert_eq!(layout.max_windows(), 8);

        // First row
        assert_eq!(layout.calculate_position(0), Rect::new(0, 0, 960, 270));
        assert_eq!(layout.calculate_position(1), Rect::new(960, 0, 960, 270));

        // Second row
        assert_eq!(layout.calculate_position(2), Rect::new(0, 270, 960, 270));
        assert_eq!(layout.calculate_position(3), Rect::new(960, 270, 960, 270));
    }

    #[test]
    fn test_grid_layout_with_offset() {
        // Secondary display at x=1920
        let display = Rect::new(1920, 0, 1920, 1080);
        let layout = GridLayout::new(2, 2, display);

        // Top-left of secondary display
        assert_eq!(layout.calculate_position(0), Rect::new(1920, 0, 960, 540));
        // Top-right of secondary display
        assert_eq!(layout.calculate_position(1), Rect::new(2880, 0, 960, 540));
    }

    #[test]
    fn test_calculate_all_positions() {
        let display = Rect::new(0, 0, 800, 600);
        let layout = GridLayout::new(2, 2, display);

        let positions = layout.calculate_all_positions(3);
        assert_eq!(positions.len(), 3);
        assert_eq!(positions[0], Rect::new(0, 0, 400, 300));
        assert_eq!(positions[1], Rect::new(400, 0, 400, 300));
        assert_eq!(positions[2], Rect::new(0, 300, 400, 300));
    }
}
