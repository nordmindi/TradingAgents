# Asset Handling Fixes for Production Builds

## Problem
The logo `vein-logo-text.webp` was not appearing in PDF reports when the application was built in production, although it was visible in development. This was because:

1. The `assets` folder was not included in the package distribution
2. The PDF generation script was using a simple path resolution that only worked in development environments

## Solution

### 1. Updated Package Configuration
Modified `pyproject.toml` to include the assets folder in the package data:

```toml
[tool.setuptools.package-data]
cli = ["static/*"]
"*" = ["assets/*", "assets/**/*"]
```

### 2. Enhanced Asset Path Resolution
Updated `scripts/generate_full_report_pdf.py` to properly locate assets in both development and production environments by checking multiple possible paths:

```python
# Try to find the assets folder in different possible locations
# 1. In the current working directory (development)
# 2. In the package installation directory (production)
possible_paths = [
    os.path.join(os.getcwd(), "assets", "vein-logo-text.webp"),
    os.path.join(os.path.dirname(__file__), "..", "assets", "vein-logo-text.webp"),
    os.path.join(sys.prefix, "assets", "vein-logo-text.webp"),
    os.path.join(getattr(sys, '_MEIPASS', ''), "assets", "vein-logo-text.webp"),
]

self.logo_path = None
for path in possible_paths:
    if os.path.exists(path):
        self.logo_path = path
        break

# If still not found, try to find it relative to the package
if self.logo_path is None:
    # Try to find the package root
    package_root = Path(__file__).parent.parent
    asset_path = package_root / "assets" / "vein-logo-text.webp"
    if asset_path.exists():
        self.logo_path = str(asset_path)
```

### 3. Updated Dockerfile
Modified `Dockerfile.service` to ensure the assets folder is copied during the build process:

```dockerfile
COPY --chown=app:app pyproject.toml README.md ./
COPY --chown=app:app tradingagents/ tradingagents/
COPY --chown=app:app cli/ cli/
COPY --chown=app:app scripts/ scripts/
COPY --chown=app:app assets/ assets/
```

### 4. Added Null Checks
Updated the PDF generation code to handle cases where the logo might not be found:

```python
if self.logo_path and os.path.exists(self.logo_path):
    self.image(self.logo_path, x=17, y=8, w=29)
```

## Testing
Created test scripts to verify that:
1. Assets can be found in various environments
2. The PDF generator can properly locate the logo asset

## Result
The logo should now appear correctly in PDF reports in both development and production environments.