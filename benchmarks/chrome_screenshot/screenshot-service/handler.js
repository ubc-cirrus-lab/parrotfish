const puppeteer = require("puppeteer-core");
const chromium = require("@sparticuz/chromium");

const capture = async (event) => {
  const { queryStringParameters } = event;
  if (!queryStringParameters || !queryStringParameters.url || !queryStringParameters.screen) {
    return { statusCode: 400 };
  }

  const { url } = queryStringParameters;
  const [width, height] = queryStringParameters.screen.split(",");

  if (!width || !height) {
    return { statusCode: 400 };
  }

  const executablePath = await chromium.executablePath();
  const browser = await puppeteer.launch({
    args: chromium.args,
    defaultViewport: chromium.defaultViewport,
    executablePath: executablePath,
    headless: true,
    ignoreHTTPSErrors: true,
    timeout: 0,
  });

  const page = await browser.newPage();

  await page.goto(url, {
    waitUntil: "load",
    timeout: 0,
  });

  const title = await page.title();
  const screenshot = await page.screenshot({ encoding: "base64" });
  
  console.log("Success: ", screenshot);
  return {
    statusCode: 200,
    body: `<img src="data:image/png;base64,${screenshot}">`,
    headers: { "Content-Type": "text/html" }
  };
}

module.exports = { capture };
