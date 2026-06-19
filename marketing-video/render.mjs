/*
 * 逐帧导出：用系统 Chrome 驱动 canvas，按固定时间步渲染，再用 ffmpeg 合成 MP4。
 * 用法: node render.mjs [--fps 30] [--scale 1]
 */
import puppeteer from "puppeteer-core";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

const FPS = parseInt(arg("fps", "30"), 10);
const DURATION = 5.0;
const TOTAL = Math.round(FPS * DURATION);
const framesDir = path.join(__dirname, "frames");
const distDir = path.join(__dirname, "dist");
const outFile = path.join(distDir, "endoscope-marketing.mp4");

const CHROME =
  process.env.CHROME_PATH ||
  ["/usr/local/bin/google-chrome", "/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]
    .find((p) => existsSync(p)) || "/usr/local/bin/google-chrome";

function run(cmd, args) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: "inherit" });
    p.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`${cmd} exited ${code}`))));
  });
}

async function main() {
  await rm(framesDir, { recursive: true, force: true });
  await mkdir(framesDir, { recursive: true });
  await mkdir(distDir, { recursive: true });

  console.log(`Chrome: ${CHROME}`);
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--force-color-profile=srgb",
      "--hide-scrollbars",
      "--allow-file-access-from-files",
      "--disable-web-security",
      "--window-size=1920,1080",
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  const url = pathToFileURL(path.join(__dirname, "index.html")).href;
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.waitForFunction("window.__ready === true", { timeout: 30000 });
  // 字体彻底就绪
  await new Promise((r) => setTimeout(r, 400));

  console.log(`Rendering ${TOTAL} frames @ ${FPS}fps ...`);
  for (let i = 0; i < TOTAL; i++) {
    const t = i / FPS;
    const dataUrl = await page.evaluate((tt) => {
      window.__renderFrame(tt);
      return document.getElementById("c").toDataURL("image/png");
    }, t);
    const b64 = dataUrl.replace(/^data:image\/png;base64,/, "");
    const name = path.join(framesDir, `f${String(i).padStart(4, "0")}.png`);
    await writeFile(name, Buffer.from(b64, "base64"));
    if (i % 15 === 0) process.stdout.write(`  ${i}/${TOTAL}\r`);
  }
  console.log(`\nFrames done.`);
  await browser.close();

  console.log("Encoding MP4 with ffmpeg ...");
  await run("ffmpeg", [
    "-y",
    "-framerate", String(FPS),
    "-i", path.join(framesDir, "f%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-profile:v", "high",
    "-crf", "18",
    "-movflags", "+faststart",
    outFile,
  ]);

  // 同时导出一张封面图（首个有内容的帧）
  await run("ffmpeg", [
    "-y",
    "-i", path.join(framesDir, "f0090.png"),
    path.join(distDir, "poster.png"),
  ]).catch(() => {});

  console.log(`\n✅ 完成: ${outFile}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
