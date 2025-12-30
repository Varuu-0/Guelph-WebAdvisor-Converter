# Guelph-WebAdvisor-Converter

A desktop utility for University of Guelph students to transform WebAdvisor schedule exports into a visual, color-coded weekly calendar. 

The application parses the Ellucian JSON data embedded in the "Print Schedule" view and generates a CSS Grid-based HTML file. This file includes a built-in function to export the calendar as a high-resolution PNG for mobile use.

## Installation & Setup

### For General Users (Executable)
1. Navigate to the [Releases](releases) section of this repository.
2. Download the latest `GuelphConverter.exe`.
3. Run the executable (no Python installation required).

### For Developers (Source Code)
1. Ensure you have Python 3.10+ installed.
2. Install dependencies:
   ```bash
   pip install customtkinter beautifulsoup4
   ```
3. Run the script:
   ```bash
   python ScheduleApp.py
   ```

### Building the Executable
If you wish to build the standalone `.exe` yourself, use **PyInstaller**:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Generate the executable using the following command:
   ```bash
   pyinstaller --noconsole --onefile ScheduleApp.py
   ```
   *Note: `--noconsole` prevents a terminal window from popping up behind the GUI, and `--onefile` bundles everything into a single executable.*
3. Once finished, the `.exe` will be located in the newly created `dist/` folder.

## Workflow: How to get the Input File

The converter requires a specific HTML export from the WebAdvisor portal to function correctly:

1.  Log in to **WebAdvisor**.
2.  Navigate to: **Academics** > **Student Planning** > **Plan, Schedule, Register & Drop**.
3.  Select the desired semester (e.g., Winter 2026).
4.  Click the **Print** button (this opens a tab with the URL starting with `.../PrintSchedule`).
5.  In the new print preview tab, press **Ctrl + S** (Windows) or **Cmd + S** (Mac).
6.  Save the file. Ensure the file type is set to **Webpage, HTML Only**.

## Usage

1. Launch the application (`GuelphConverter.exe` or `ScheduleApp.py`).
2. Click **Select saved Schedule.html** and choose the file saved in the steps above.
3. Click **Generate & Open Calendar**.
4. The utility will generate `my_calendar.html` in the same directory and automatically open it in your default web browser.
5. Click the **📸 Save as Image** button within the browser to download a PNG version.

## Technical Specifications

- **Parsing Engine:** `BeautifulSoup4` + `re` regex to extract the `var result` JSON object used by the Ellucian platform.
- **GUI:** `customtkinter` (Dark Mode native).
- **Styling:** Dynamic CSS Grid with a hashing-based pastel color generator to ensure consistent course coloring.
- **Client-Side Export:** Integrates the `html-to-image` JavaScript library via CDN for high-quality browser-side rendering.

## Privacy & Safety

*   **Local Processing:** All data parsing occurs locally on your machine. No schedule data is uploaded to external servers or tracking services.
*   **Data Warning:** Your raw WebAdvisor HTML and the generated `my_calendar.html` contain personal information including your **Full Name** and **Student ID**. Do not share these files publicly or upload them to a public GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).
