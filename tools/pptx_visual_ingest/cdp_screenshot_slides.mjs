import { spawn } from 'node:child_process';
import { mkdtemp, rm, mkdir, writeFile, readFile, access } from 'node:fs/promises';
import { constants } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { pathToFileURL } from 'node:url';

const [htmlPath, outDir, prefix = 'slide', chromePathArg] = process.argv.slice(2);
if (!htmlPath || !outDir) {
  console.error('usage: node cdp_screenshot_slides.mjs Preview.html outDir [prefix] [chromePath]');
  process.exit(2);
}

const chromePath = chromePathArg || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const profile = await mkdtemp(path.join(os.tmpdir(), 'chrome-cdp-'));
await mkdir(outDir, { recursive: true });

const chrome = spawn(chromePath, [
  '--headless=new',
  '--disable-gpu',
  '--hide-scrollbars',
  '--no-first-run',
  '--no-default-browser-check',
  '--allow-file-access-from-files',
  '--disable-web-security',
  `--user-data-dir=${profile}`,
  '--remote-debugging-port=0',
  'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe'] });

chrome.stderr.on('data', () => {});

async function waitFile(p, timeout = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      await access(p, constants.R_OK);
      return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out waiting for ${p}`);
}

try {
  const portFile = path.join(profile, 'DevToolsActivePort');
  await waitFile(portFile);
  const [port] = (await readFile(portFile, 'utf8')).trim().split(/\n/);
  const fileUrl = pathToFileURL(path.resolve(htmlPath)).href;
  const resp = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(fileUrl)}`, { method: 'PUT' });
  if (!resp.ok) throw new Error(`json/new failed ${resp.status}: ${await resp.text()}`);
  const target = await resp.json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true });
    ws.addEventListener('error', reject, { once: true });
  });

  let id = 0;
  const pending = new Map();
  ws.addEventListener('message', (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    }
  });

  function send(method, params = {}) {
    const mid = ++id;
    ws.send(JSON.stringify({ id: mid, method, params }));
    return new Promise((resolve, reject) => pending.set(mid, { resolve, reject }));
  }

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1600,
    height: 1200,
    deviceScaleFactor: 2,
    mobile: false,
  });
  await send('Page.navigate', { url: fileUrl });
  await new Promise((resolve) => setTimeout(resolve, 1500));

  const evalRes = await send('Runtime.evaluate', {
    returnByValue: true,
    expression: `(() => Array.from(document.querySelectorAll('div.slide')).map((el, i) => {
      const r = el.getBoundingClientRect();
      return {
        index: i + 1,
        x: r.x,
        y: r.y,
        width: r.width,
        height: r.height,
        imgCount: el.querySelectorAll('img').length,
        text: (el.innerText || '').trim()
      };
    }))()`,
  });

  const slides = evalRes.result.value;
  await writeFile(path.join(outDir, 'slides-meta.json'), JSON.stringify(slides, null, 2));

  for (const slide of slides) {
    const data = await send('Page.captureScreenshot', {
      format: 'png',
      fromSurface: true,
      captureBeyondViewport: true,
      clip: {
        x: slide.x,
        y: slide.y,
        width: slide.width,
        height: slide.height,
        scale: 1,
      },
    });
    const fname = path.join(outDir, `${prefix}-${String(slide.index).padStart(3, '0')}.png`);
    await writeFile(fname, Buffer.from(data.data, 'base64'));
  }

  ws.close();
  console.log(JSON.stringify({ slides: slides.length, outDir }));
} finally {
  chrome.kill('SIGTERM');
  await rm(profile, { recursive: true, force: true });
}
