import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const publicDir = path.join(__dirname, '..', 'public');
const faviconSvg = path.join(publicDir, 'favicon.svg');
const icon192Svg = path.join(publicDir, 'icon-192.svg');
const icon512Svg = path.join(publicDir, 'icon-512.svg');

// Sizes for favicons
const faviconSizes = [16, 32, 48];
const pwaIconSizes = [192, 512];
const appleTouchIconSize = 180;

async function generateIcons() {
  console.log('Generating PNG icons from SVG...\n');

  // Generate standard favicon sizes (16x16, 32x32, 48x48)
  for (const size of faviconSizes) {
    const outputPath = path.join(publicDir, `favicon-${size}x${size}.png`);
    await sharp(faviconSvg)
      .resize(size, size)
      .png()
      .toFile(outputPath);
    console.log(`✓ Generated ${size}x${size} favicon`);
  }

  // Generate Apple touch icon (180x180)
  const appleTouchPath = path.join(publicDir, 'apple-touch-icon.png');
  await sharp(faviconSvg)
    .resize(appleTouchIconSize, appleTouchIconSize)
    .png()
    .toFile(appleTouchPath);
  console.log(`✓ Generated ${appleTouchIconSize}x${appleTouchIconSize} apple-touch-icon`);

  // Generate PWA icons (192x192, 512x512)
  for (const size of pwaIconSizes) {
    const svgSource = size === 192 ? icon192Svg : icon512Svg;
    const outputPath = path.join(publicDir, `icon-${size}x${size}.png`);
    await sharp(svgSource)
      .resize(size, size)
      .png()
      .toFile(outputPath);
    console.log(`✓ Generated ${size}x${size} PWA icon`);
  }

  // Generate favicon.ico (multi-size ICO file)
  console.log('\nGenerating favicon.ico...');
  
  // For favicon.ico, we'll use the 32x32 version as the main icon
  // Note: Creating a proper multi-size .ico requires additional libraries
  // For now, we'll create a 32x32 PNG that can be renamed to .ico
  const favicon32Path = path.join(publicDir, 'favicon-32x32.png');
  const faviconIcoPath = path.join(publicDir, 'favicon.ico');
  
  // Copy the 32x32 PNG as favicon.ico (browsers will accept PNG format even with .ico extension)
  fs.copyFileSync(favicon32Path, faviconIcoPath);
  console.log('✓ Generated favicon.ico');

  console.log('\n✅ All icons generated successfully!');
}

generateIcons().catch(console.error);
