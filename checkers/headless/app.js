const puppeteer = require("puppeteer");
const express = require("express");
const { response } = require("express");
const app = express();
const port = 3000;
app.use(express.json());

const http = require("http");
const server = http.createServer(app);
const { Server } = require("socket.io");
const io = new Server(server);

let base_url = "";

if (process.env.DEBUG) {
  base_url = "http://172.17.0.1:3003";
  base_url = "http://localhost:3003";
} else {
  base_url = "http://10.60." + process.env.TEAM_ID + ".1:3003";
}

app.get("/", async (req, res) => {
  res.send("Alive");
});

io.on("connection", async (socket) => {
  console.log("Checker connected.");
  // starts chrome

  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--user-agent=" + getRandomUserAgent()],
    //slowMo: 50,
    //headless: true,
    ignoreHTTPSErrors: true,
  });

  console.log("Browser started.");
  const page = await browser.newPage();
  await page.setDefaultNavigationTimeout(10000);
  await page.setDefaultTimeout(10000);

  await page.setRequestInterception(true);
  page.on("request", (req) => {
    if (req.resourceType() === "image") req.abort();
    else req.continue();
  });
  console.log("Page opened.");
  socket.on("disconnect", async () => {
    console.log("Checker disconnected. Closing the browser.");
    const pages = await browser.pages();
    await Promise.all(pages.map((page) => page.close())).catch(() =>
      browser.close()
    );
    await browser.close();
  });

  socket.on("register", async (msg, ack) => {
    console.log("Registering user.");
    res = await register(page, msg["username"], msg["password"])
      .then((res) => res)
      .catch((e) => {
        return { error: true, msg_err: e.stack };
      });
    ack(res);
    socket.emit("user_registered");
    console.log("User registerd. Errors:", res["error"]);
  });

  socket.on("visit", async (msg, ack) => {
    err = await visit(page, msg)
      .then((res) => res)
      .catch((e) => {
        return { error: true, msg_err: e };
      });
    ack(err);
  });

  socket.on("login", async (msg) => {
    console.log("Login user.");
    err = await login(
      page,
      msg["username"],
      msg["password"],
      msg["private_key"]
    )
      .then((res) => res)
      .catch((e) => {
        return { error: true, msg_err: e };
      });
    console.log("User login ended. Errors:", res["error"]);
    return err;
  });

  socket.on("buy", async (msg) => {
    console.log("Buy of nft " + msg["nft_id"] + " started");
    err = await buy(page, msg["nft_id"])
      .then((res) => res)
      .catch((e) => {
        return { error: true, msg_err: e };
      });

    console.log("Finished buying nft. Errors:", res["error"]);
    socket.emit("buyed");
    return err;
  });

  socket.on("donate", async (msg) => {
    console.log(
      "Donate nft " + msg["nft_id"] + " to " + msg["to"] + " started"
    );
    err = await donate(page, msg["nft_id"], msg["to"])
      .then((res) => res)
      .catch((e) => {
        return { error: true, msg_err: e };
      });
    console.log("Finished donating nft. Errors:", res["error"], err);
    socket.emit("donated");
    return err;
  });
  console.log("Headless ready.");
  socket.emit("ready");
});
server.listen(port, () => {
  console.log(`Headless listening at http://0.0.0.0:${port}`);
});

async function visit(page, url) {
  await page.goto(url);
  //await page.waitForTimeout(5000)

  return { error: false };
}

async function login(page, username, password, private_key) {
  await visit(page, base_url + "/login");

  await page.type("#login_username", username);
  await page.type("#login_password", password);
  await page.type("#private_key", private_key);

  await Promise.all([
    page.click("#login_submit"),
    page.waitForNavigation({ waitUntil: "networkidle2" }),
  ]);
  const page_data = await page.evaluate(
    () => document.querySelector("*").outerHTML
  );

  return {
    error: !page_data.includes(username),
  };
}

async function register(page, username, password) {
  await visit(page, base_url + "/register");

  await page.type("#register_username", username);
  await page.type("#register_password", password);
  //await page.click('#open_private_modal');
  await page.evaluate(() => {
    UI_create_key();
  });
  const private_key = await page.evaluate(
    () => document.querySelector("#private_ui").innerHTML
  );
  const close_button = await page.$("#modal_close");
  await close_button.evaluate((b) => b.click());
  const submit_button = await page.$("#register_submit");
  //throw puppeteer.TimeoutError;
  // submit form, and wait
  await Promise.all([
    submit_button.evaluate((b) => b.click()),
    page.waitForNavigation({ waitUntil: "networkidle2" }),
  ]);

  // A couple of checks...
  const page_data = await page.evaluate(
    () => document.querySelector("*").outerHTML
  );

  errors = !page_data.includes(username);

  return {
    error: errors,
    private_key: private_key,
  };
}

async function buy(page, id) {
  await visit(page, base_url + "/view/" + id);

  const buy_submit = await page.$("#buy_submit");
  await Promise.all([
    buy_submit.evaluate((b) => b.click()),
    page.waitForNavigation({ waitUntil: "networkidle2" }),
  ]);

  return {
    error: false,
  };
}

async function donate(page, id, to) {
  await visit(page, base_url + "/view/" + id);
  await page.evaluate((to) => {
    document.querySelector("#to_addr").value = to;
  }, to);

  await Promise.all([
    page.evaluate(() => {
      donate();
    }),
    page.waitForNavigation({ waitUntil: "networkidle2" }),
  ]);
  const page_data = await page.evaluate(
    () => document.querySelector("*").outerHTML
  );

  return {
    error: !page_data.includes("Succesfully donated!"),
  };
}

const fs = require("fs").promises;
// note this will be async
lines = fs.readFile("user-agents.txt", "utf-8").then((content) => {
  lines = content.split("\n");
});

function getRandomUserAgent() {
  // choose one of the lines...
  var line = lines[Math.floor(Math.random() * lines.length)];

  return line;
}
