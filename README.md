# Safe Deal - Browser

Safe Deal - Browser is a secure, privacy-focused browser based on Chromium that includes the Safe Deal Shopping Assistant extension by default. This browser enhances users' online shopping experience with features like price tracking, fake review detection, and seller analysis.

## Features

1. **Pre-installed Safe Deal Shopping Assistant:**

   - Integrated Safe Deal Shopping Assistant extension
   - Compatible with Amazon, AliExpress, and eBay for enhanced shopping insights

2. **Privacy and Security Focus:**

   - Built-in ad-blocking and anti-tracking features
   - HTTPS enforcement and end-to-end encryption for all browsing activities

3. **Customizable Interface:**
   - Modifiable browser themes
   - Configurable shopping assistant settings directly from the browser interface

## Development Setup

### Prerequisites

- macOS
- Xcode
- Homebrew
- Python3
- git

### Setting up the Development Environment

1. Clone the Safe Deal - Browser repository:

   ```bash
   git clone https://github.com/your-username/safe-deal-browser.git
   cd safe-deal-browser
   ```

2. Run the setup script:

   ```bash
   ./tools/setup.sh
   ```

   This script will:

   - Install necessary dependencies
   - Clone the Chromium repository as a submodule
   - Set up the development environment

3. Build Chromium:

   ```bash
   ./tools/build.sh
   ```

4. Set up the Safe Deal Shopping Assistant Extension:

   - Copy the extension files to `src/safe_deal/extension`

5. Modify Chromium to include the extension:

   - Update `chromium/src/chrome/browser/extensions/external_component_loader.cc`
   - Create and update `chromium/src/chrome/common/safe_deal_constants.h` and `chromium/src/chrome/common/safe_deal_constants.cc`

6. Rebuild Chromium:

   ```bash
   ./tools/build.sh
   ```

7. Run the modified browser:
   ```bash
   ./chromium/src/out/Default/Chromium.app/Contents/MacOS/Chromium
   ```

## Contributing

We welcome contributions to the Safe Deal - Browser project. Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

- Chromium Project
- Safe Deal Shopping Assistant developers
