import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { chromium } from "@playwright/test";
import sharp from "sharp";

const root = fileURLToPath(new URL("../", import.meta.url));
process.chdir(root);
const output = resolve("assets/profile");
const frames = resolve("shots/profile-frames");
await mkdir(output, { recursive: true });
await mkdir(frames, { recursive: true });

if (process.argv[2]) {
  await sharp(resolve(process.argv[2])).rotate().resize({ width: 1000, withoutEnlargement: true }).jpeg({ quality: 91, mozjpeg: true }).toFile(resolve(output, "portrait.jpg"));
}
const portrait = `data:image/jpeg;base64,${(await readFile(resolve(output, "portrait.jpg"))).toString("base64")}`;

async function font(family) {
  const response = await fetch(`https://fonts.googleapis.com/css2?family=${family}&display=swap`, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!response.ok) throw new Error(`Font stylesheet failed: ${family}`);
  const css = await response.text();
  const url = css.match(/src:\s*url\((https:\/\/fonts\.gstatic\.com\/[^)]+)\)/)?.[1];
  if (!url) throw new Error(`No self-contained font source: ${family}`);
  const binary = await fetch(url);
  if (!binary.ok) throw new Error(`Font download failed: ${family}`);
  return `data:font/ttf;base64,${Buffer.from(await binary.arrayBuffer()).toString("base64")}`;
}

const sans = await font("DM+Sans:wght@600");
const serif = await font("Instrument+Serif:ital@1");
const devanagari = await font("Noto+Serif+Devanagari:wght@400");
const fonts = `@font-face{font-family:Body;src:url('${sans}')}@font-face{font-family:Editorial;src:url('${serif}');font-style:italic}@font-face{font-family:Devanagari;src:url('${devanagari}')}`;
const pointer = '<svg width="27" height="32" viewBox="0 0 27 32" xmlns="http://www.w3.org/2000/svg"><path d="M2 2L24 14L14 18L10 29Z" fill="currentColor" stroke="#0b0a11" stroke-width="1.5" stroke-linejoin="round"/></svg>';

// This offscreen composition is an asset renderer, not a shipped web experience.
const html = `<!doctype html><meta charset="utf-8"><style>${fonts}
*{box-sizing:border-box;margin:0;letter-spacing:0}body{width:1200px;height:560px;overflow:hidden;background:#0b0a11;color:#f5f0ed;font-family:Body,sans-serif}.hero{position:relative;width:1200px;height:560px;isolation:isolate}.identity{position:absolute;left:58px;top:52px;font-size:17px}.identity:before{content:'*';color:#f44984;font-size:30px;margin-right:12px;vertical-align:middle}.headlines{position:absolute;left:58px;top:143px;z-index:2}.line{font-size:75px;line-height:1.13;overflow:hidden;width:720px}.line>span{display:block}.second{font-size:65px;line-height:1.25}.second em{font:italic 91px/1 Editorial,serif;color:#ff865a}.tagline{position:absolute;left:61px;top:365px;font:italic 36px/1.2 Editorial,serif;color:#c7b0dc}.footer{position:absolute;left:60px;right:60px;bottom:31px;display:flex;justify-content:space-between;border-top:1px solid #39313f;padding-top:18px;color:#b9afc1;font-size:13px}.footer>span:last-child{color:#d1b479}.portrait{position:absolute;width:292px;height:330px;left:824px;top:98px;transform:rotate(-5deg)}.photo,.fragment{position:absolute;inset:0;background:url('${portrait}') center/cover}.photo{border:1px solid #766477}.fragment{opacity:0}.fragment:nth-child(1){clip-path:polygon(0 0,50.1% 0,50.1% 50.1%,0 50.1%)}.fragment:nth-child(2){clip-path:polygon(49.9% 0,100% 0,100% 50.1%,49.9% 50.1%)}.fragment:nth-child(3){clip-path:polygon(0 49.9%,50.1% 49.9%,50.1% 100%,0 100%)}.fragment:nth-child(4){clip-path:polygon(49.9% 49.9%,100% 49.9%,100% 100%,49.9% 100%)}.frame{position:absolute;inset:-7px;border:1px solid #a783f0;opacity:0}.frame i{position:absolute;width:7px;height:7px;background:#f5f0ed;border:1px solid #a783f0}.frame i:nth-child(1){left:-4px;top:-4px}.frame i:nth-child(2){right:-4px;top:-4px}.frame i:nth-child(3){left:-4px;bottom:-4px}.frame i:nth-child(4){right:-4px;bottom:-4px}.note{position:absolute;left:849px;top:450px;font:italic 24px Editorial,serif;color:#d9c6b5}.cursor{position:absolute;left:0;top:0;opacity:0;z-index:5;color:#ff865a}.cursor label{position:absolute;left:22px;top:26px;background:currentColor;border-radius:2px;padding:3px 7px;white-space:nowrap;font-size:10px}.cursor label span{color:#0b0a11}.cursor:nth-child(2){color:#bc9af8}.cursor:nth-child(3){color:#f579a7}.cursor:nth-child(4){color:#c8b083}.cursor i{position:absolute;left:-9px;top:-8px;width:28px;height:28px;border:1px solid currentColor;border-radius:50%;opacity:0}
</style><div class="hero"><div class="identity">Rudransh Singh</div><div class="headlines"><div class="line"><span>I'm Rudransh.</span></div><div class="line second"><span>But <em>Ruru</em> works.</span></div></div><div class="tagline">Curiosity into capability.</div><div class="portrait"><div class="photo"></div><div class="fragments">${[0,1,2,3].map(() => '<div class="fragment"></div>').join("")}</div><div class="frame"><i></i><i></i><i></i><i></i></div></div><div class="note">A little curiosity goes a long way.</div><div class="cursors">${["curiosity","a little chaos","instinct","precision"].map((name) => `<div class="cursor">${pointer}<label><span>${name}</span></label><i></i></div>`).join("")}</div><div class="footer"><span>Computer Science & Engineering · PSIT, Kanpur</span><span>Still learning. Always building.</span></div></div><script>
const clamp=v=>Math.max(0,Math.min(1,v));const ease=v=>1-Math.pow(1-clamp(v),3);const mix=(a,b,p)=>a+(b-a)*p;
window.renderFrame=t=>{
 const ready=t<0||t>=4.25;const entering=clamp(t/0.25);const settle=ease((t-3.05)/.8);const pieces=[[-235,-160,-18],[220,-125,25],[-200,180,-22],[175,190,17]];
 document.querySelector('.photo').style.opacity=ready?1:0;document.querySelector('.portrait').style.transform='rotate('+(-5*settle)+'deg)';
 document.querySelector('.frame').style.opacity=ready?0:clamp(t/.3)*(1-clamp((t-3.05)/.3));
 document.querySelector('.note').style.opacity=ready?1:settle;
 const text=document.querySelectorAll('.line>span');text.forEach((el,i)=>{const p=ready?1:ease((t-3.12-i*.15)/.65);el.style.transform='translateY('+((1-p)*110)+'%)';el.style.opacity=p});document.querySelector('.tagline').style.opacity=ready?1:ease((t-3.55)/.6);
 const starts=[.25,.65,1.12,1.65],durations=[.85,1.05,1.1,.85];
 document.querySelectorAll('.fragment').forEach((el,i)=>{const p=ease((t-starts[i])/durations[i]);const s=pieces[i];let x=s[0]*(1-p),y=s[1]*(1-p),r=s[2]*(1-p);if(i===2&&t>1.85&&t<2.75){const wobble=Math.sin(clamp((t-1.85)/.9)*Math.PI);x+=14*wobble;r+=9*wobble}if(i===1&&t>2.65&&t<3.15){x+=4*Math.sin(clamp((t-2.65)/.5)*Math.PI)}el.style.opacity=ready?0:Math.min(1,p*5);el.style.transform='translate('+x+'px,'+y+'px) rotate('+r+'deg)'});
 document.querySelectorAll('.cursor').forEach((el,i)=>{const p=ease((t-starts[i]+.12)/durations[i]);const corners=[[823,96],[982,112],[828,284],[982,284]],s=pieces[i],target=corners[i];let x=target[0]+s[0]*(1-p),y=target[1]+s[1]*(1-p)-Math.sin(p*Math.PI)*28;if(i===0&&t>2.4){const p2=ease((t-2.4)/.55);x=mix(x,980,p2);y=mix(y,264,p2)}if(i===3&&t>2.45){const p2=ease((t-2.45)/.4);x=mix(x,960,p2);y=mix(y,283,p2)}el.style.opacity=ready?0:clamp((t-starts[i]+.1)*5)*(1-clamp((t-3.15)/.35));el.style.transform='translate('+x+'px,'+y+'px)';const click=Math.sin(clamp((t-2.95)/.25)*Math.PI);el.querySelector('i').style.opacity=i===0?click:0;el.querySelector('i').style.transform='scale('+(1+click)+')'});
 if(ready)document.querySelector('.portrait').style.transform='rotate(-5deg)';
};window.renderFrame(-1);
</script>`;

const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 560 }, deviceScaleFactor: 1 });
  await page.setContent(html);
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(async () => { const images=[...document.images]; await Promise.all(images.map(image => image.decode())); });
  await page.locator(".portrait").screenshot({ path: resolve("shots/portrait-proof.png") });
  await page.screenshot({ path: resolve(output, "hero-static.png") });
  await page.screenshot({ path: resolve(frames, "000.png") });
  const durations = [800];
  for (let i = 0; i <= 54; i++) {
    await page.evaluate((t) => window.renderFrame(t), i * 4.25 / 54);
    await page.screenshot({ path: resolve(frames, `${String(i+1).padStart(3,"0")}.png`) });
    durations.push(i===54?1200:80);
  }
  await writeFile(resolve(frames, "timing.json"), JSON.stringify(durations));
  const encoded = spawnSync(process.env.PYTHON || "python", ["scripts/encode_profile_gif.py", frames], { stdio: "inherit" });
  if (encoded.status !== 0) throw new Error("GIF encoding failed");

  for (const mobile of [false, true]) {
    const width=mobile?780:1200, height=mobile?850:620;
    await page.setViewportSize({ width, height });
    await page.setContent(`<!doctype html><meta charset="utf-8"><style>${fonts}*{box-sizing:border-box;margin:0;letter-spacing:0}body{background:#100e12;color:#d9c18d;text-align:center;width:${width}px;height:${height}px;padding:${mobile?65:58}px ${mobile?44:80}px;font-family:Body,sans-serif}.kicker{font-size:${mobile?20:14}px;color:#b5a27b;margin-bottom:${mobile?45:35}px}.verse{font:400 ${mobile?43:40}px/1.9 Devanagari,'Nirmala UI',serif;white-space:nowrap}.meaning{font-size:${mobile?26:19}px;color:#c1b6a3;line-height:1.7;max-width:${mobile?610:830}px;margin:${mobile?38:25}px auto 0}.tagline{font:italic ${mobile?54:43}px/1.2 Editorial,serif;margin-top:${mobile?54:35}px}.name{font-size:${mobile?22:15}px;margin-top:${mobile?31:25}px;color:#bcac8e}.nickname{font:italic ${mobile?60:45}px/1.2 Editorial,serif;margin-top:10px;color:#eee4d1}</style><p class="kicker">A thought I come back to.</p><div class="verse" lang="sa">कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।<br>मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥</div><p class="kicker" style="margin:18px 0 0">Bhagavad Gita · 2.47</p><p class="meaning">You have the right to action alone, never to its fruits.<br>${mobile?"":"Do not make the fruits of action your motive,<br>"}${mobile?"Do not make the fruits of action your motive, nor be attached to inaction.":"nor be attached to inaction."}</p><p class="tagline">Curiosity into capability.</p><p class="name">Rudransh Singh</p><p class="nickname">Ruru</p>`);
    await page.evaluate(() => document.fonts.ready);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth||document.documentElement.scrollHeight>innerHeight);
    if(overflow) throw new Error(`Closing composition overflow: ${mobile?"mobile":"desktop"}`);
    await page.screenshot({ path: resolve(output, mobile?"closing-mobile.png":"closing.png") });
  }

  for (const [id,url] of [["gdgoc","https://gdgoc-community-website.vercel.app"],["bloodbond","https://akakrish.github.io/BloodBond/"]]) {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const response=await page.goto(url,{waitUntil:"networkidle",timeout:60000});
    if(!response?.ok()) throw new Error(`Public preview unavailable: ${url}`);
    await page.waitForTimeout(4000);
    await sharp(await page.screenshot({animations:"disabled"})).resize(900).jpeg({quality:87,mozjpeg:true}).toFile(resolve(output,`${id}-preview.jpg`));
  }
  console.log("Profile graphics rendered from the real portrait and actual public previews.");
} finally { await browser.close(); }
