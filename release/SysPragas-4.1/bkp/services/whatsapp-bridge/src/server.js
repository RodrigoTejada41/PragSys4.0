"use strict";

const fs = require("fs");
const path = require("path");
const express = require("express");
const QRCode = require("qrcode");
const pino = require("pino");
const {
  default: makeWASocket,
  Browsers,
  DisconnectReason,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  useMultiFileAuthState,
} = require("@whiskeysockets/baileys");

const logger = pino({
  level: process.env.WHATSAPP_BRIDGE_LOG_LEVEL || "info",
});

const app = express();
app.use(express.json({ limit: "1mb" }));

const BRIDGE_PORT = Number(process.env.WHATSAPP_BRIDGE_PORT || 3100);
const BRIDGE_HOST = process.env.WHATSAPP_BRIDGE_HOST || "0.0.0.0";
const BRIDGE_API_KEY = String(process.env.WHATSAPP_BRIDGE_API_KEY || "").trim();
const SESSION_ROOT = path.resolve(process.env.WHATSAPP_BRIDGE_SESSION_DIR || path.join(process.cwd(), "sessions"));
fs.mkdirSync(SESSION_ROOT, { recursive: true });

const sessions = new Map();

function readApiKey(req) {
  const authHeader = String(req.headers.authorization || "").trim();
  if (authHeader.toLowerCase().startsWith("bearer ")) {
    return authHeader.slice(7).trim();
  }
  return String(req.headers.apikey || req.headers["x-api-key"] || "").trim();
}

function requireApiKey(req, res, next) {
  if (!BRIDGE_API_KEY) {
    return next();
  }
  if (readApiKey(req) !== BRIDGE_API_KEY) {
    return res.status(401).json({
      status: "ERROR",
      error: true,
      message: "API key invalida para o WhatsApp Bridge.",
    });
  }
  return next();
}

app.use(requireApiKey);

function normalizePhone(input) {
  const digits = String(input || "").replace(/\D+/g, "");
  if (!digits) {
    throw new Error("Numero de telefone obrigatorio.");
  }
  if (digits.length < 12) {
    throw new Error("Numero de telefone invalido para envio.");
  }
  return `${digits}@s.whatsapp.net`;
}

function getSessionState(instanceName) {
  return sessions.get(instanceName);
}

function getSessionPath(instanceName) {
  return path.join(SESSION_ROOT, instanceName);
}

async function buildQrDataUrl(rawQr) {
  if (!rawQr) {
    return null;
  }
  return QRCode.toDataURL(rawQr, {
    errorCorrectionLevel: "M",
    margin: 2,
    scale: 6,
  });
}

async function setQrPayload(session, qr) {
  session.qr = qr || null;
  session.qrImageDataUrl = qr ? await buildQrDataUrl(qr) : null;
  session.status = qr ? "connecting" : session.status;
}

async function ensureSession(instanceName) {
  const existing = getSessionState(instanceName);
  if (existing && existing.socket) {
    return existing;
  }

  const authFolder = getSessionPath(instanceName);
  fs.mkdirSync(authFolder, { recursive: true });
  const { state, saveCreds } = await useMultiFileAuthState(authFolder);
  const { version } = await fetchLatestBaileysVersion();

  const session = {
    instanceName,
    status: "connecting",
    socket: null,
    qr: null,
    qrImageDataUrl: null,
    connectedPhone: null,
    pairingCode: null,
    lastError: null,
    authFolder,
    restartTimer: null,
  };
  sessions.set(instanceName, session);

  const socket = makeWASocket({
    version,
    auth: {
      creds: state.creds,
      keys: makeCacheableSignalKeyStore(state.keys, logger),
    },
    browser: Browsers.windows("SysPragas"),
    printQRInTerminal: false,
    logger,
    syncFullHistory: false,
    markOnlineOnConnect: false,
  });

  session.socket = socket;

  socket.ev.on("creds.update", saveCreds);
  socket.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      await setQrPayload(session, qr);
      session.lastError = null;
    }
    if (connection === "open") {
      session.status = "open";
      session.qr = null;
      session.qrImageDataUrl = null;
      session.pairingCode = null;
      session.connectedPhone = socket.user?.id || null;
      session.lastError = null;
      logger.info({ instanceName, phone: session.connectedPhone }, "WhatsApp Bridge connected");
      return;
    }
    if (connection === "close") {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      session.status = shouldReconnect ? "connecting" : "closed";
      session.connectedPhone = null;
      session.lastError = lastDisconnect?.error?.message || null;
      session.socket = null;
      if (shouldReconnect) {
        clearTimeout(session.restartTimer);
        session.restartTimer = setTimeout(() => {
          ensureSession(instanceName).catch((error) => {
            logger.error({ err: error, instanceName }, "Failed to reconnect WhatsApp Bridge session");
          });
        }, 2000);
      }
    }
  });

  return session;
}

function serializeStatus(session) {
  if (!session) {
    return {
      instance: {
        instanceName: null,
        state: "closed",
        ownerJid: null,
      },
      status: "closed",
      message: "Sessao WhatsApp ainda nao iniciada.",
    };
  }
  return {
    instance: {
      instanceName: session.instanceName,
      state: session.status,
      ownerJid: session.connectedPhone,
    },
    status: session.status,
    pairingCode: session.pairingCode,
    qrcode: session.qr,
    base64: session.qrImageDataUrl ? session.qrImageDataUrl.replace(/^data:image\/png;base64,/, "") : null,
    message: session.lastError || (session.status === "open" ? "Sessao ativa." : "Leia o QR Code para conectar."),
  };
}

async function destroySession(instanceName) {
  const session = getSessionState(instanceName);
  if (!session) {
    return;
  }
  clearTimeout(session.restartTimer);
  sessions.delete(instanceName);
  try {
    await session.socket?.logout();
  } catch (error) {
    logger.warn({ err: error, instanceName }, "WhatsApp Bridge logout returned error");
  }
  try {
    await session.socket?.end?.();
  } catch (error) {
    logger.warn({ err: error, instanceName }, "WhatsApp Bridge socket end returned error");
  }
}

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "whatsapp-bridge", driver: "baileys" });
});

app.get("/instance/connectionState/:instance", async (req, res) => {
  const instanceName = req.params.instance;
  const session = getSessionState(instanceName);
  if (!session) {
    return res.json(serializeStatus(null));
  }
  return res.json(serializeStatus(session));
});

app.get("/instance/connect/:instance", async (req, res) => {
  try {
    const instanceName = req.params.instance;
    const session = await ensureSession(instanceName);
    if (session.qr && !session.qrImageDataUrl) {
      session.qrImageDataUrl = await buildQrDataUrl(session.qr);
    }
    return res.json(serializeStatus(session));
  } catch (error) {
    logger.error({ err: error, instance: req.params.instance }, "Failed to create WhatsApp Bridge session");
    return res.status(500).json({
      status: "ERROR",
      error: true,
      message: error.message || "Nao foi possivel iniciar a sessao do WhatsApp.",
    });
  }
});

app.delete("/instance/logout/:instance", async (req, res) => {
  const instanceName = req.params.instance;
  await destroySession(instanceName);
  return res.json({
    status: "SUCCESS",
    error: false,
    response: {
      message: "Instance logged out",
    },
  });
});

app.post("/message/sendText/:instance", async (req, res) => {
  try {
    const instanceName = req.params.instance;
    const session = await ensureSession(instanceName);
    if (session.status !== "open" || !session.socket) {
      return res.status(409).json({
        status: "ERROR",
        error: true,
        message: "Sessao WhatsApp ainda nao conectada. Gere e leia o QR Code.",
      });
    }
    const jid = normalizePhone(req.body.number || req.body.to);
    const text = String(req.body.text || req.body.message || "").trim();
    if (!text) {
      return res.status(400).json({
        status: "ERROR",
        error: true,
        message: "Mensagem obrigatoria para envio.",
      });
    }
    const sent = await session.socket.sendMessage(jid, { text });
    return res.json({
      status: "SUCCESS",
      error: false,
      key: {
        id: sent.key?.id || null,
      },
      response: sent,
    });
  } catch (error) {
    logger.error({ err: error, instance: req.params.instance }, "Failed to send WhatsApp message");
    return res.status(500).json({
      status: "ERROR",
      error: true,
      message: error.message || "Falha ao enviar mensagem pelo WhatsApp.",
    });
  }
});

app.listen(BRIDGE_PORT, BRIDGE_HOST, () => {
  logger.info({ host: BRIDGE_HOST, port: BRIDGE_PORT }, "WhatsApp Bridge running");
});

