import { useEffect, useState, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { io, Socket } from 'socket.io-client';

interface ClientInfo {
  pushname?: string;
  wid?: {
    user?: string;
  };
}

interface WhatsAppStatus {
  authenticated: boolean;
  ready: boolean;
  hasQR: boolean;
  clientInfo?: ClientInfo;
}

interface WhatsAppQRCodeProps {
  bridgeUrl?: string;
  onAuthenticated?: () => void;
  onReady?: (info: ClientInfo) => void;
  onError?: (error: string) => void;
}

export const WhatsAppQRCode: React.FC<WhatsAppQRCodeProps> = ({
  bridgeUrl = 'http://localhost:8765',
  onAuthenticated,
  onReady,
  onError,
}) => {
  const [qrCode, setQRCode] = useState<string | null>(null);
  const [status, setStatus] = useState<WhatsAppStatus>({
    authenticated: false,
    ready: false,
    hasQR: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const socket = io(bridgeUrl, {
      transports: ['websocket', 'polling'],
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[WhatsApp] WebSocket connected');
      setLoading(false);
      setError(null);
    });

    socket.on('connect_error', (err) => {
      console.error('[WhatsApp] WebSocket connection error:', err);
      setError('Cannot connect to WhatsApp bridge service. Make sure the Node.js bridge is running.');
      setLoading(false);
      onError?.('Connection failed');
    });

    socket.on('status', (data: WhatsAppStatus) => {
      console.log('[WhatsApp] Status update:', data);
      setStatus(data);
    });

    socket.on('qr', (data: { qr: string }) => {
      console.log('[WhatsApp] QR code received');
      setQRCode(data.qr);
      setStatus(prev => ({ ...prev, hasQR: true }));
    });

    socket.on('authenticated', () => {
      console.log('[WhatsApp] Authenticated');
      setQRCode(null);
      setStatus(prev => ({ ...prev, authenticated: true, hasQR: false }));
      onAuthenticated?.();
    });

    socket.on('auth_failure', (data: { message: string }) => {
      console.error('[WhatsApp] Authentication failed:', data.message);
      setError(`Authentication failed: ${data.message}`);
      onError?.(data.message);
    });

    socket.on('ready', (data: { info: ClientInfo }) => {
      console.log('[WhatsApp] Ready:', data.info);
      setStatus(prev => ({ ...prev, ready: true, clientInfo: data.info }));
      onReady?.(data.info);
    });

    socket.on('disconnected', (data: { reason: string }) => {
      console.log('[WhatsApp] Disconnected:', data.reason);
      setStatus({ authenticated: false, ready: false, hasQR: false });
      setQRCode(null);
    });

    socket.on('disconnect', () => {
      console.log('[WhatsApp] WebSocket disconnected');
    });

    // Fetch initial status
    fetchStatus();

    return () => {
      socket.disconnect();
    };
  }, [bridgeUrl, onAuthenticated, onReady, onError]);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${bridgeUrl}/status`);
      const data = await response.json();
      setStatus(data);
      
      // If not authenticated, try to get QR code
      if (!data.authenticated && !data.hasQR) {
        const qrResponse = await fetch(`${bridgeUrl}/qr`);
        if (qrResponse.ok) {
          const qrData = await qrResponse.json();
          if (qrData.qr) {
            setQRCode(qrData.qr);
          }
        }
      }
    } catch (err) {
      console.error('[WhatsApp] Error fetching status:', err);
      setError('Failed to fetch WhatsApp status');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${bridgeUrl}/logout`, { method: 'POST' });
      setStatus({ authenticated: false, ready: false, hasQR: false });
      setQRCode(null);
      // Restart to get new QR
      await fetch(`${bridgeUrl}/restart`, { method: 'POST' });
    } catch (err) {
      console.error('[WhatsApp] Error logging out:', err);
      setError('Failed to logout');
    }
  };

  const handleRestart = async () => {
    try {
      setLoading(true);
      await fetch(`${bridgeUrl}/restart`, { method: 'POST' });
      setQRCode(null);
      setError(null);
      setTimeout(() => setLoading(false), 2000);
    } catch (err) {
      console.error('[WhatsApp] Error restarting:', err);
      setError('Failed to restart');
      setLoading(false);
    }
  };

  return (
    <div className="whatsapp-qr-container" style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>
          <span style={styles.icon}>💬</span>
          WhatsApp Web
        </h2>
        {status.ready && status.clientInfo && (
          <div style={styles.userInfo}>
            <span style={styles.statusIndicator}>●</span>
            Connected as: {status.clientInfo.pushname} ({status.clientInfo.wid?.user})
          </div>
        )}
      </div>

      {loading && (
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}></div>
          <p>Connecting to WhatsApp bridge...</p>
        </div>
      )}

      {error && (
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>⚠️ {error}</p>
          <div style={styles.errorHelp}>
            <p>To fix this:</p>
            <ol>
              <li>Open a terminal in the WhatsApp bridge directory</li>
              <li>Run: <code>npm install && npm start</code></li>
              <li>Wait for the bridge to start</li>
              <li>Refresh this page</li>
            </ol>
          </div>
          <button onClick={handleRestart} style={styles.button}>
            Retry Connection
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {!status.authenticated && qrCode && (
            <div style={styles.qrContainer}>
              <div style={styles.instructions}>
                <h3>Scan QR Code with WhatsApp</h3>
                <ol style={styles.stepsList}>
                  <li>Open WhatsApp on your phone</li>
                  <li>Tap Menu <span style={styles.menuIcon}>⋮</span> or Settings <span style={styles.settingsIcon}>⚙️</span></li>
                  <li>Tap <strong>Linked Devices</strong></li>
                  <li>Tap <strong>Link a Device</strong></li>
                  <li>Point your phone at this screen to scan the code</li>
                </ol>
              </div>
              
              <div style={styles.qrCodeWrapper}>
                <QRCodeSVG
                  value={qrCode}
                  size={280}
                  level="M"
                  includeMargin={true}
                  style={styles.qrCode}
                />
              </div>

              <div style={styles.qrNote}>
                <p>⏱️ QR code expires in ~20 seconds</p>
                <p>If it expires, a new one will be generated automatically</p>
              </div>
            </div>
          )}

          {!status.authenticated && !qrCode && !loading && (
            <div style={styles.waitingContainer}>
              <div style={styles.spinner}></div>
              <p>Waiting for QR code...</p>
              <button onClick={handleRestart} style={styles.button}>
                Generate QR Code
              </button>
            </div>
          )}

          {status.authenticated && !status.ready && (
            <div style={styles.successContainer}>
              <div style={styles.successIcon}>✓</div>
              <p style={styles.successText}>Authenticated!</p>
              <p>Initializing WhatsApp client...</p>
            </div>
          )}

          {status.ready && (
            <div style={styles.successContainer}>
              <div style={styles.successIcon}>✓</div>
              <p style={styles.successText}>WhatsApp is connected!</p>
              <p>You can now receive and send messages through the agent.</p>
              
              <div style={styles.actionsContainer}>
                <button onClick={handleLogout} style={{...styles.button, ...styles.logoutButton}}>
                  Logout
                </button>
              </div>
              
              <div style={styles.tipContainer}>
                <h4>💡 Tips:</h4>
                <ul>
                  <li>Send a message to your WhatsApp number to test</li>
                  <li>The agent will respond automatically</li>
                  <li>Group chats are supported</li>
                  <li>You can send and receive media files</li>
                </ul>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    textAlign: 'center',
    marginBottom: '30px',
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#25D366',
    marginBottom: '10px',
  },
  icon: {
    fontSize: '32px',
    marginRight: '10px',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontSize: '14px',
    color: '#666',
  },
  statusIndicator: {
    color: '#25D366',
    fontSize: '20px',
    lineHeight: '1',
  },
  loadingContainer: {
    textAlign: 'center',
    padding: '40px',
  },
  spinner: {
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #25D366',
    borderRadius: '50%',
    width: '50px',
    height: '50px',
    animation: 'spin 1s linear infinite',
    margin: '0 auto 20px',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    border: '1px solid #ef5350',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '20px',
  },
  errorText: {
    color: '#c62828',
    fontWeight: 'bold',
    marginBottom: '15px',
  },
  errorHelp: {
    backgroundColor: '#fff',
    padding: '15px',
    borderRadius: '4px',
    marginBottom: '15px',
    fontSize: '14px',
  },
  qrContainer: {
    textAlign: 'center',
  },
  instructions: {
    marginBottom: '30px',
    textAlign: 'left',
  },
  stepsList: {
    paddingLeft: '20px',
    lineHeight: '1.8',
  },
  menuIcon: {
    fontSize: '18px',
  },
  settingsIcon: {
    fontSize: '16px',
  },
  qrCodeWrapper: {
    display: 'flex',
    justifyContent: 'center',
    padding: '20px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    border: '2px solid #25D366',
    marginBottom: '20px',
  },
  qrCode: {
    display: 'block',
  },
  qrNote: {
    fontSize: '14px',
    color: '#666',
    fontStyle: 'italic',
  },
  waitingContainer: {
    textAlign: 'center',
    padding: '40px',
  },
  successContainer: {
    textAlign: 'center',
    padding: '40px',
  },
  successIcon: {
    fontSize: '64px',
    color: '#25D366',
    marginBottom: '20px',
  },
  successText: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#25D366',
    marginBottom: '10px',
  },
  actionsContainer: {
    marginTop: '30px',
  },
  button: {
    backgroundColor: '#25D366',
    color: 'white',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '6px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  logoutButton: {
    backgroundColor: '#dc3545',
  },
  tipContainer: {
    marginTop: '30px',
    padding: '20px',
    backgroundColor: '#e3f2fd',
    borderRadius: '8px',
    textAlign: 'left',
  },
};

// Add keyframes for spinner animation
const styleSheet = document.styleSheets[0];
const keyframes =
  `@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }`;

try {
  styleSheet.insertRule(keyframes, styleSheet.cssRules.length);
} catch {
  // Ignore if already added
}

export default WhatsAppQRCode;
