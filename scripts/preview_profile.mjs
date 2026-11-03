import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { resolve, extname, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { chromium } from "@playwright/test";

const root = fileURLToPath(new URL("../", import.meta.url));
process.chdir(root);
await mkdir("shots", { recursive: true });
const rendered = execFileSync("gh", ["api", "markdown", "--method", "POST", "-f", "mode=gfm", "-f", "context=akaKRISH/akaKRISH", "-F", "text=@README.md"], { encoding: "utf8", maxBuffer: 2_000_000 });
assert(!/<script\b|<iframe\b|<canvas\b/i.test(rendered));
assert(rendered.includes('media="(prefers-reduced-motion: reduce)"'));
assert(rendered.includes('media="(max-width: 600px)"'));
await writeFile("shots/readme-github.html", rendered);

const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage();
  await page.goto("https://github.com/akaKRISH/akaKRISH", { waitUntil: "domcontentloaded" });
  const css = await page.locator('link[rel="stylesheet"]').evaluateAll((links) => links.map((link) => link.href));
  const html = (theme) => `<!doctype html><html lang="en" data-color-mode="${theme}" data-light-theme="light" data-dark-theme="dark"><meta charset="utf-8">${css.map((url)=>`<link rel="stylesheet" href="${url}">`).join("")}<style>body{margin:0;padding:32px 20px;background:var(--bgColor-default,#0d1117)}article.markdown-body{width:100%;max-width:860px;padding:28px;margin:0 auto;border:1px solid var(--borderColor-default,#30363d);border-radius:6px}article img{max-width:100%}@media(max-width:600px){body{padding:16px 12px}article.markdown-body{padding:20px 16px}}</style><article class="markdown-body">${rendered}</article></html>`;
  let previewHtml = html("dark");
  const types={".png":"image/png",".gif":"image/gif",".jpg":"image/jpeg",".svg":"image/svg+xml"};
  await page.route("https://profile-preview.invalid/**",async(route)=>{
    const pathname=decodeURIComponent(new URL(route.request().url()).pathname);
    if(pathname==="/"){await route.fulfill({contentType:"text/html; charset=utf-8",body:previewHtml});return;}
    const path=resolve(root,`.${pathname}`);
    assert(path.startsWith(`${root.replace(/[\\/]$/,"")}${sep}`),"Path outside checkout");
    try{await route.fulfill({contentType:types[extname(path)]||"application/octet-stream",body:await readFile(path)});}catch{await route.fulfill({status:404,body:"Not found"});}
  });
  const failures=[];
  page.on("pageerror",error=>failures.push(error.message));
  for(const [width,theme] of [[1280,"dark"],[375,"dark"],[375,"light"],[1280,"light"]]){
    previewHtml=html(theme);
    await page.setViewportSize({width,height:900});
    await page.emulateMedia({reducedMotion:"reduce",colorScheme:theme});
    await page.goto("https://profile-preview.invalid/",{waitUntil:"networkidle"});
    await page.locator("img").evaluateAll(images=>Promise.all(images.map(image=>image.decode())));
    assert.equal(await page.locator("h1").textContent(),"Rudransh Singh");
    assert((await page.locator('img[src$="hero-assembly.gif"]').evaluate(image=>image.currentSrc)).endsWith("hero-static.png"));
    assert((await page.locator('img[src$="closing.png"]').evaluate(image=>image.currentSrc)).endsWith(width<600?"closing-mobile.png":"closing.png"));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Horizontal overflow: ${width} ${theme}`);
    await page.screenshot({path:`shots/readme-${width}-${theme}.png`,fullPage:true});
    for(const summary of await page.locator("summary").all()) await summary.click();
    await page.locator("img").evaluateAll(images=>Promise.all(images.map(image=>image.decode())));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Expanded details overflow: ${width} ${theme}`);
    await page.screenshot({path:`shots/readme-expanded-${width}-${theme}.png`,fullPage:true});
  }
  await page.emulateMedia({reducedMotion:"no-preference",colorScheme:"dark"});
  previewHtml=html("dark");
  await page.setViewportSize({width:1280,height:900});
  await page.goto("https://profile-preview.invalid/",{waitUntil:"networkidle"});
  const hero=page.locator('img[src$="hero-assembly.gif"]');
  assert((await hero.evaluate(image=>image.currentSrc)).endsWith("hero-assembly.gif"));
  const before=await hero.screenshot();
  await page.waitForTimeout(1600);
  const during=await hero.screenshot({path:"shots/hero-browser-animation.png"});
  assert(!before.equals(during),"Browser did not play the GIF");
  await page.waitForTimeout(6000);
  const final=await hero.screenshot();
  await page.waitForTimeout(800);
  assert(final.equals(await hero.screenshot()),"GIF is not stable after its one-shot ending");
  assert.deepEqual(failures,[]);
  console.log("PASS: GitHub-sanitized HTML; desktop/mobile light/dark; all images; reduced motion; mobile Sanskrit; one-shot browser playback; collapsed/expanded layouts");

  if(process.argv.includes("--github")){
    const url="https://github.com/akaKRISH/akaKRISH/tree/codex/profile-origin";
    for(const width of [1280,375]){
      await page.setViewportSize({width,height:900});
      await page.emulateMedia({reducedMotion:"reduce",colorScheme:"dark"});
      await page.goto(url,{waitUntil:"networkidle",timeout:60000});
      const readme=page.locator("article.markdown-body").filter({hasText:"Things I Had to Try"}).first();
      await readme.waitFor();
      await readme.scrollIntoViewIfNeeded();
      await readme.locator("details").evaluateAll(elements=>elements.forEach(element=>{element.open=true}));
      await readme.locator("img").evaluateAll(images=>Promise.all(images.map(image=>{image.loading="eager";return image.decode()})));
      const distorted=await readme.locator("img").evaluateAll(images=>images.filter(image=>{const bounds=image.getBoundingClientRect();return bounds.width>0&&bounds.height>0&&image.naturalWidth>0&&Math.abs(bounds.width/bounds.height-image.naturalWidth/image.naturalHeight)>.015}).map(image=>image.alt));
      assert.deepEqual(distorted,[],`Distorted GitHub images at ${width}px`);
      assert(await readme.evaluate(element=>element.scrollWidth<=element.clientWidth+1),`GitHub README overflow: ${width}`);
      const liveHero=readme.getByRole("img",{name:/^I'm Rudransh/});
      assert(await liveHero.evaluate(image=>image.currentSrc===new URL(image.closest("picture").querySelector("source").srcset,document.baseURI).href),"GitHub did not select the motion fallback");
      const closing=readme.getByRole("img",{name:/^Bhagavad Gita 2.47:/});
      assert(await closing.evaluate((image,mobile)=>mobile?image.currentSrc===new URL(image.closest("picture").querySelector("source").srcset,document.baseURI).href:image.currentSrc===image.src,width<600),"GitHub did not select the expected Sanskrit composition");
      await readme.locator("details").evaluateAll(elements=>elements.forEach(element=>{element.open=false}));
      await readme.screenshot({path:`shots/github-readme-${width}.png`});
      if(width===1280){
        await page.emulateMedia({reducedMotion:"no-preference",colorScheme:"dark"});
        await liveHero.evaluate(image=>{const url=new URL(image.src);url.searchParams.set("playback-check",Date.now());image.src=url.href;return image.decode()});
        await liveHero.scrollIntoViewIfNeeded();
        const first=await liveHero.screenshot();
        await page.waitForTimeout(1600);
        assert(!first.equals(await liveHero.screenshot({path:"shots/github-hero-playing.png"})),"GitHub-served GIF did not animate");
      }
    }
    console.log("PASS: real GitHub branch-rendered README; desktop/mobile decoded assets; reduced-motion and mobile picture sources; live GIF playback");
  }
}finally{await browser.close();}
