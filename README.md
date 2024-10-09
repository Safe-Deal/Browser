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

1. Install Depot Tools:

   ```bash
   git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
   ```

   Add Depot Tools to your PATH in `~/.bash_profile` or `~/.zshrc`:

   ```bash
   export PATH="$PATH:/path/to/depot_tools"
   ```

2. Clone the Chromium repository:

   ```bash
   mkdir chromium && cd chromium
   fetch chromium
   ```

3. Install additional build dependencies:

   ```bash
   cd src
   ./build/install-build-deps.sh
   ```

4. Configure the build:

   ```bash
   gn args out/Default
   ```

   Add the following configuration:

   ```
   is_debug = false
   is_component_build = false
   symbol_level = 0
   ```

5. Build Chromium:

   ```bash
   autoninja -C out/Default chrome
   ```

6. Set up the Safe Deal Shopping Assistant Extension:

   - Download the extension from the Chrome Web Store
   - Extract the files to `src/chrome/browser/resources/safe_deal_extension`

7. Modify Chromium to include the extension:

   - Update `src/chrome/browser/extensions/external_component_loader.cc`
   - Create and update `src/chrome/common/safe_deal_constants.h` and `src/chrome/common/safe_deal_constants.cc`

8. Rebuild Chromium:

   ```bash
   autoninja -C out/Default chrome
   ```

9. Run the modified browser:
   ```bash
   out/Default/Chromium.app/Contents/MacOS/Chromium
   ```

## Contributing

We welcome contributions to the Safe Deal - Browser project. Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgments

- Chromium Project
- Safe Deal Shopping Assistant developers
