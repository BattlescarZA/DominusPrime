#!/usr/bin/env node
/**
 * WhatsApp Web Bridge Service
 * Provides WhatsApp Web functionality via HTTP/WebSocket API
 * Uses whatsapp-web.js for WhatsApp integration
 */

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const fs = require('fs');

// Configuration
const PORT = process.env.WHATSAPP_BRIDGE_PORT || 8765;
const SESSION_DIR = process.env.WHATSAPP_SESSION_DIR || path.join(process.env.HOME || process.env.USERPROFILE, '.dominusprime', 'whatsapp', 'session');

// Ensure session directory exists
if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

app.use(express.json());

// State
let whatsappClient = null;
let currentQRCode = null;
let isAuthenticated = false;
let isReady = false;
let clientInfo = null;

// Initialize WhatsApp client
function initializeClient() {
    console.log('[WhatsApp Bridge] Initializing client...');
    
    whatsappClient = new Client({
        authStrategy: new LocalAuth({
            clientId: 'dominusprime',
            dataPath: SESSION_DIR
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        }
    });

    // Event: QR Code generated
    whatsappClient.on('qr', (qr) => {
        console.log('[WhatsApp Bridge] QR Code received');
        currentQRCode = qr;
        io.emit('qr', { qr });
    });

    // Event: Authentication success
    whatsappClient.on('authenticated', () => {
        console.log('[WhatsApp Bridge] Authenticated successfully');
        isAuthenticated = true;
        currentQRCode = null;
        io.emit('authenticated', { success: true });
    });

    // Event: Authentication failure
    whatsappClient.on('auth_failure', (msg) => {
        console.error('[WhatsApp Bridge] Authentication failed:', msg);
        isAuthenticated = false;
        io.emit('auth_failure', { message: msg });
    });

    // Event: Client ready
    whatsappClient.on('ready', async () => {
        console.log('[WhatsApp Bridge] Client is ready');
        isReady = true;
        
        try {
            clientInfo = whatsappClient.info;
            console.log(`[WhatsApp Bridge] Connected as: ${clientInfo.pushname} (${clientInfo.wid.user})`);
        } catch (error) {
            console.error('[WhatsApp Bridge] Error getting client info:', error);
        }
        
        io.emit('ready', { info: clientInfo });
    });

    // Event: Incoming message
    whatsappClient.on('message', async (message) => {
        try {
            const chat = await message.getChat();
            const contact = await message.getContact();
            
            const messageData = {
                id: message.id._serialized,
                body: message.body,
                from: message.from,
                to: message.to,
                timestamp: message.timestamp,
                hasMedia: message.hasMedia,
                type: message.type,
                isGroup: chat.isGroup,
                chatId: chat.id._serialized,
                chatName: chat.name,
                contactId: contact.id._serialized,
                contactName: contact.name || contact.pushname,
                isFromMe: message.fromMe
            };

            // Download media if present
            if (message.hasMedia) {
                try {
                    const media = await message.downloadMedia();
                    if (media) {
                        messageData.media = {
                            mimetype: media.mimetype,
                            data: media.data, // Base64
                            filename: media.filename
                        };
                    }
                } catch (error) {
                    console.error('[WhatsApp Bridge] Error downloading media:', error);
                }
            }

            io.emit('message', messageData);
        } catch (error) {
            console.error('[WhatsApp Bridge] Error processing message:', error);
        }
    });

    // Event: Message creation (outgoing)
    whatsappClient.on('message_create', async (message) => {
        if (message.fromMe) {
            io.emit('message_sent', {
                id: message.id._serialized,
                body: message.body,
                to: message.to,
                timestamp: message.timestamp
            });
        }
    });

    // Event: Disconnected
    whatsappClient.on('disconnected', (reason) => {
        console.log('[WhatsApp Bridge] Disconnected:', reason);
        isAuthenticated = false;
        isReady = false;
        io.emit('disconnected', { reason });
    });

    // Initialize
    whatsappClient.initialize().catch((error) => {
        console.error('[WhatsApp Bridge] Initialization error:', error);
    });
}

// REST API Endpoints

// Get status
app.get('/status', (req, res) => {
    res.json({
        authenticated: isAuthenticated,
        ready: isReady,
        hasQR: !!currentQRCode,
        clientInfo: clientInfo
    });
});

// Get QR code
app.get('/qr', (req, res) => {
    if (currentQRCode) {
        res.json({
            qr: currentQRCode,
            authenticated: isAuthenticated
        });
    } else if (isAuthenticated) {
        res.json({
            qr: null,
            authenticated: true,
            message: 'Already authenticated'
        });
    } else {
        res.status(404).json({
            error: 'QR code not available yet'
        });
    }
});

// Send message
app.post('/send', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready' });
    }

    try {
        const { chatId, message, mediaPath, mediaOptions } = req.body;

        if (!chatId) {
            return res.status(400).json({ error: 'chatId is required' });
        }

        let result;
        
        if (mediaPath) {
            // Send media
            const media = MessageMedia.fromFilePath(mediaPath);
            result = await whatsappClient.sendMessage(chatId, media, mediaOptions || {});
        } else if (message) {
            // Send text
            result = await whatsappClient.sendMessage(chatId, message);
        } else {
            return res.status(400).json({ error: 'message or mediaPath is required' });
        }

        res.json({
            success: true,
            messageId: result.id._serialized
        });
    } catch (error) {
        console.error('[WhatsApp Bridge] Send error:', error);
        res.status(500).json({
            error: error.message
        });
    }
});

// Get chat by ID
app.get('/chat/:chatId', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready' });
    }

    try {
        const chat = await whatsappClient.getChatById(req.params.chatId);
        res.json({
            id: chat.id._serialized,
            name: chat.name,
            isGroup: chat.isGroup,
            unreadCount: chat.unreadCount
        });
    } catch (error) {
        res.status(404).json({ error: 'Chat not found' });
    }
});

// Set typing state
app.post('/typing/:chatId', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready' });
    }

    try {
        const chat = await whatsappClient.getChatById(req.params.chatId);
        await chat.sendStateTyping();
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Logout
app.post('/logout', async (req, res) => {
    try {
        if (whatsappClient) {
            await whatsappClient.logout();
            isAuthenticated = false;
            isReady = false;
            currentQRCode = null;
            clientInfo = null;
        }
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Restart
app.post('/restart', async (req, res) => {
    try {
        if (whatsappClient) {
            await whatsappClient.destroy();
        }
        initializeClient();
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

// WebSocket connection
io.on('connection', (socket) => {
    console.log('[WhatsApp Bridge] Client connected via WebSocket');
    
    // Send current state
    socket.emit('status', {
        authenticated: isAuthenticated,
        ready: isReady,
        hasQR: !!currentQRCode
    });
    
    if (currentQRCode && !isAuthenticated) {
        socket.emit('qr', { qr: currentQRCode });
    }

    socket.on('disconnect', () => {
        console.log('[WhatsApp Bridge] Client disconnected');
    });
});

// Start server
server.listen(PORT, () => {
    console.log(`[WhatsApp Bridge] Server running on http://localhost:${PORT}`);
    console.log(`[WhatsApp Bridge] Session directory: ${SESSION_DIR}`);
    console.log('[WhatsApp Bridge] Initializing WhatsApp client...');
    initializeClient();
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('[WhatsApp Bridge] Shutting down...');
    if (whatsappClient) {
        await whatsappClient.destroy();
    }
    server.close(() => {
        console.log('[WhatsApp Bridge] Server closed');
        process.exit(0);
    });
});

process.on('SIGTERM', async () => {
    console.log('[WhatsApp Bridge] Terminating...');
    if (whatsappClient) {
        await whatsappClient.destroy();
    }
    server.close(() => {
        console.log('[WhatsApp Bridge] Server closed');
        process.exit(0);
    });
});
