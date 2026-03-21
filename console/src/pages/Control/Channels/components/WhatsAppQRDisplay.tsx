import { useEffect, useState, useCallback } from "react";
import { Alert, Card } from "@agentscope-ai/design";
import { Spin } from "antd";
import { CheckCircleFilled, QrcodeOutlined } from "@ant-design/icons";
import { QRCodeSVG } from 'qrcode.react';

interface WhatsAppQRDisplayProps {
  channelKey: string;
  enabled: boolean;
}

interface WhatsAppStatus {
  qr_code: string | null;
  authenticated: boolean;
  status: string;
}

export function WhatsAppQRDisplay({ channelKey, enabled }: WhatsAppQRDisplayProps) {
  const [status, setStatus] = useState<WhatsAppStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQRCode = useCallback(async () => {
    if (channelKey !== "whatsapp" || !enabled) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/whatsapp/qr");
      if (!response.ok) {
        throw new Error(`Failed to fetch QR code: ${response.statusText}`);
      }

      const data: WhatsAppStatus = await response.json();
      setStatus(data);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error";
      setError(errorMsg);
      console.error("Failed to fetch WhatsApp QR code:", err);
    } finally {
      setLoading(false);
    }
  }, [channelKey, enabled]);

  useEffect(() => {
    if (channelKey !== "whatsapp" || !enabled) {
      setStatus(null);
      return;
    }

    // Initial fetch
    fetchQRCode();

    // Poll every 3 seconds while not authenticated
    const intervalId = setInterval(() => {
      if (!status?.authenticated) {
        fetchQRCode();
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [channelKey, enabled, status?.authenticated, fetchQRCode]);

  if (channelKey !== "whatsapp" || !enabled) {
    return null;
  }

  return (
    <div style={{ marginTop: 16 }}>
      <Card
        size="small"
        title={
          <span>
            <QrcodeOutlined style={{ marginRight: 8 }} />
            WhatsApp Web Authentication
          </span>
        }
      >
        {loading && !status && (
          <div style={{ textAlign: "center", padding: 24 }}>
            <Spin size="large" tip="Connecting to WhatsApp bridge..." />
          </div>
        )}

        {error && (
          <Alert
            type="warning"
            showIcon
            message="Connection Error"
            description={
              <div>
                <p>{error}</p>
                <p style={{ marginTop: 8, marginBottom: 0 }}>
                  <strong>Make sure:</strong>
                </p>
                <ol style={{ marginTop: 4, marginBottom: 0, paddingLeft: 20 }}>
                  <li>WhatsApp channel is enabled</li>
                  <li>Node.js bridge service is running (see console logs)</li>
                  <li>Run: <code>cd src/dominusprime/app/channels/whatsapp && npm install && npm start</code></li>
                </ol>
              </div>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        {status?.authenticated ? (
          <Alert
            type="success"
            showIcon
            icon={<CheckCircleFilled />}
            message="WhatsApp Connected!"
            description="Your WhatsApp account is authenticated and ready to use. You can now send messages to your WhatsApp number and the agent will respond."
          />
        ) : status?.qr_code ? (
          <div>
            <Alert
              type="info"
              showIcon
              message="Scan QR Code with WhatsApp"
              description={
                <div>
                  <p style={{ marginBottom: 8 }}>Follow these steps:</p>
                  <ol style={{ marginBottom: 0, paddingLeft: 20 }}>
                    <li>Open WhatsApp on your phone</li>
                    <li>Tap <strong>Menu</strong> (⋮) or <strong>Settings</strong> (⚙️)</li>
                    <li>Tap <strong>Linked Devices</strong></li>
                    <li>Tap <strong>Link a Device</strong></li>
                    <li>Point your phone at the QR code below</li>
                  </ol>
                </div>
              }
              style={{ marginBottom: 16 }}
            />
            <div style={{ textAlign: "center", padding: 16 }}>
              <div
                style={{
                  display: "inline-block",
                  padding: 20,
                  background: "white",
                  border: "2px solid #25D366",
                  borderRadius: 8,
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                }}
              >
                <QRCodeSVG
                  value={status.qr_code}
                  size={280}
                  level="M"
                  includeMargin={true}
                  style={{
                    display: "block",
                  }}
                />
              </div>
              <div style={{ marginTop: 16 }}>
                <div style={{ color: "#25D366", fontWeight: "bold", fontSize: 14 }}>
                  ⏱️ QR code refreshes automatically
                </div>
                <div style={{ marginTop: 4, color: "#8c8c8c", fontSize: 12 }}>
                  Scanning QR code will link your WhatsApp account
                </div>
              </div>
            </div>
          </div>
        ) : (
          !loading && (
            <div style={{ textAlign: "center", padding: 24 }}>
              <Spin size="large" tip="Generating QR code..." />
              <div style={{ marginTop: 16, color: "#8c8c8c", fontSize: 12 }}>
                Starting WhatsApp Web client... This may take a few moments.
              </div>
            </div>
          )
        )}
      </Card>
    </div>
  );
}
