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
const QR_WAIT_TIMEOUT_MS = Number(process.env.WHATSAPP_BRIDGE_QR_WAIT_TIMEOUT_MS || 8000);
const QR_RETRY_WAIT_MS = Number(process.env.WHATSAPP_BRIDGE_QR_RETRY_WAIT_MS || 2500);
const QR_TTL_MS = Number(process.env.WHATSAPP_BRIDGE_QR_TTL_MS || 60000);
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isTruthyFlag(value) {
  return ["1", "true", "yes", "y", "on"].includes(String(value || "").trim().toLowerCase());
}

function isQrExpired(session) {
  return Boolean(session?.qrExpiresAt && session.qrExpiresAt <= Date.now());
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
  session.qrIssuedAt = qr ? Date.now() : null;
  session.qrExpiresAt = qr ? session.qrIssuedAt + QR_TTL_MS : null;
  session.status = qr ? "connecting" : session.status;
  logger.info(
    {
      instanceName: session.instanceName,
      hasQr: Boolean(qr),
      expiresAt: session.qrExpiresAt ? new Date(session.qrExpiresAt).toISOString() : null,
    },
    "WhatsApp Bridge QR updated",
  );
}

function clearQrPayload(session) {
  session.qr = null;
  session.qrImageDataUrl = null;
  session.qrIssuedAt = null;
  session.qrExpiresAt = null;
}

function clearRestartTimer(session) {
  if (session?.restartTimer) {
    clearTimeout(session.restartTimer);
    session.restartTimer = null;
  }
}

function removeAuthFolder(authFolder) {
  if (!authFolder || !fs.existsSync(authFolder)) {
    return;
  }
  fs.rmSync(authFolder, { recursive: true, force: true });
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

  const session = existing || {
    instanceName,
    status: "connecting",
    socket: null,
    qr: null,
    qrImageDataUrl: null,
    qrIssuedAt: null,
    qrExpiresAt: null,
    connectedPhone: null,
    pairingCode: null,
    lastError: null,
    authFolder,
    restartTimer: null,
  };

  session.instanceName = instanceName;
  session.status = "connecting";
  session.authFolder = authFolder;
  session.lastError = null;
  sessions.set(instanceName, session);

  logger.info({ instanceName, authFolder }, "Starting WhatsApp Bridge session");

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

  socket.ev.on("creds.update", async () => {
    await saveCreds();
    logger.debug({ instanceName }, "WhatsApp Bridge credentials persisted");
  });

  socket.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;
    logger.info(
      {
        instanceName,
        connection: connection || null,
        hasQr: Boolean(qr),
        statusCode: lastDisconnect?.error?.output?.statusCode || null,
      },
      "WhatsApp Bridge connection update",
    );
    if (qr) {
      await setQrPayload(session, qr);
      session.lastError = null;
    }
    if (connection === "open") {
      session.status = "open";
      clearQrPayload(session);
      session.pairingCode = null;
      session.connectedPhone = socket.user?.id || null;
      session.lastError = null;
      clearRestartTimer(session);
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
      if (!shouldReconnect) {
        clearQrPayload(session);
        logger.warn({ instanceName, statusCode }, "WhatsApp Bridge session logged out");
        return;
      }
      clearRestartTimer(session);
      session.restartTimer = setTimeout(() => {
        ensureSession(instanceName).catch((error) => {
          logger.error({ err: error, instanceName }, "Failed to reconnect WhatsApp Bridge session");
        });
      }, 2000);
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
      expires_at: null,
      message: "Sessao WhatsApp ainda nao iniciada.",
    };
  }

  const expired = isQrExpired(session);
  return {
    instance: {
      instanceName: session.instanceName,
      state: expired && session.status !== "open" ? "qr_expired" : session.status,
      ownerJid: session.connectedPhone,
    },
    status: expired && session.status !== "open" ? "qr_expired" : session.status,
    pairingCode: session.pairingCode,
    qrcode: expired ? null : session.qr,
    base64: !expired && session.qrImageDataUrl ? session.qrImageDataUrl.replace(/^data:image\/png;base64,/, "") : null,
    expires_at: session.qrExpiresAt ? new Date(session.qrExpiresAt).toISOString() : null,
    message: session.lastError || (session.status === "open" ? "Sessao ativa." : expired ? "QR Code expirado. Gere um novo QR." : "Leia o QR Code para conectar."),
  };
}

async function destroySession(instanceName, options = {}) {
  const { purgeAuth = false } = options;
  const session = getSessionState(instanceName);
  if (!session) {
    if (purgeAuth) {
      removeAuthFolder(getSessionPath(instanceName));
    }
    return;
  }
  clearRestartTimer(session);
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
  if (purgeAuth) {
    removeAuthFolder(session.authFolder || getSessionPath(instanceName));
    logger.warn({ instanceName }, "WhatsApp Bridge auth folder purged");
  }
}

async function waitForSessionSignal(session, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (session.status === "open" || session.qr || session.lastError) {
      return;
    }
    await sleep(250);
  }
}

async function createOrRefreshSession(instanceName, { forceRefresh = false } = {}) {
  if (forceRefresh) {
    logger.warn({ instanceName }, "WhatsApp Bridge session refresh requested");
    await destroySession(instanceName, { purgeAuth: true });
  }

  let session = await ensureSession(instanceName);
  await waitForSessionSignal(session, QR_WAIT_TIMEOUT_MS);

  const needsRetry = session.status !== "open" && !session.qr;
  if (needsRetry) {
    logger.warn({ instanceName }, "WhatsApp Bridge session did not yield QR in time, retrying with clean auth");
    await destroySession(instanceName, { purgeAuth: true });
    await sleep(400);
    session = await ensureSession(instanceName);
    await waitForSessionSignal(session, QR_RETRY_WAIT_MS);
  }

  return session;
}

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "whatsapp-bridge", driver: "baileys" });
});

app.get("/instance/connectionState/:instance", async (req, res) => {
  const instanceName = req.params.instance;
  const session = getSessionState(instanceName);
  logger.info({ instanceName, state: session?.status || "closed" }, "WhatsApp Bridge status requested");
  if (!session) {
    return res.json(serializeStatus(null));
  }
  return res.json(serializeStatus(session));
});

app.get("/instance/connect/:instance", async (req, res) => {
  try {
    const instanceName = req.params.instance;
    const forceRefresh = isTruthyFlag(req.query.refresh) || isTruthyFlag(req.query.regenerate);
    const session = await createOrRefreshSession(instanceName, { forceRefresh });
    if (session.qr && !session.qrImageDataUrl) {
      session.qrImageDataUrl = await buildQrDataUrl(session.qr);
    }
    logger.info(
      {
        instanceName,
        state: session.status,
        hasQr: Boolean(session.qr || session.qrImageDataUrl),
        connectedPhone: session.connectedPhone,
      },
      "WhatsApp Bridge connect flow completed",
    );
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
  logger.warn({ instanceName }, "WhatsApp Bridge logout requested");
  await destroySession(instanceName, { purgeAuth: true });
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
      logger.warn({ instanceName, state: session.status }, "WhatsApp Bridge send rejected because session is not connected");
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
    logger.info({ instanceName, jid }, "WhatsApp Bridge sending message");
    const sent = await session.socket.sendMessage(jid, { text });
    logger.info({ instanceName, jid, messageId: sent.key?.id || null }, "WhatsApp Bridge message sent");
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
