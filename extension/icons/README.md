# Extension Icons

This folder should contain PNG icons for the Chrome extension.

## Required Icons

- `icon16.png` - 16x16 pixels (toolbar)
- `icon32.png` - 32x32 pixels (toolbar @2x)
- `icon48.png` - 48x48 pixels (extensions page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Generating Icons

You can use any image editor or online tool to create these icons.

### Option 1: Use the included SVG

Copy this SVG and convert to PNG at different sizes:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="16" fill="#2563eb"/>
  <path d="M32 32h48v8H40v28h36v8H40v28h44v8H32V32z" fill="white"/>
  <path d="M88 52l16 28H72l16-28z" fill="#60a5fa"/>
  <circle cx="88" cy="92" r="12" fill="#60a5fa"/>
</svg>
```

### Option 2: Use Online Tools

1. Go to https://www.favicon-generator.org/
2. Upload a 128x128 PNG image
3. Download the generated icon pack

### Option 3: Use ImageMagick

```bash
# If you have a 128x128 source image:
convert icon128.png -resize 48x48 icon48.png
convert icon128.png -resize 32x32 icon32.png
convert icon128.png -resize 16x16 icon16.png
```

## Temporary Solution

The extension will work without custom icons - Chrome will use a default icon.
Add your icons later to customize the appearance.
