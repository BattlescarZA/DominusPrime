import sharp from 'sharp';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const publicDir = path.join(__dirname, '..', 'public');
const logoSvg = path.join(publicDir, 'dominusprime-logo.svg');

async function generateLogoPng() {
  console.log('Generating logo.png from dominusprime-logo.svg...\n');

  // Generate a high-quality PNG logo (600x200 source, output at good resolution)
  const outputPath = path.join(publicDir, 'logo.png');
  await sharp(logoSvg)
    .resize(600, 200)
    .png()
    .toFile(outputPath);
  
  console.log('✓ Generated logo.png (600x200)');
  console.log('\n✅ Logo generated successfully!');
}

generateLogoPng().catch(console.error);
