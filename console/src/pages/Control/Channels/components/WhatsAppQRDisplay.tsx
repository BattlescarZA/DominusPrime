import { useEffect, useState, useCallback } from "react";
import { Alert, Card } from "@agentscope-ai/design";
import { Spin } from "antd";
import { CheckCircleFilled, QrcodeOutlined } from "@ant-design/icons";

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
            WhatsApp Authentication
          </span>
        }
      >
        {loading && !status && (
          <div style={{ textAlign: "center", padding: 24 }}>
            <Spin size="large" tip="Loading WhatsApp status..." />
          </div>
        )}

        {error && (
          <Alert
            type="warning"
            showIcon
            message="Connection Error"
            description={`${error}. Make sure the WhatsApp channel is enabled and the service is running.`}
            style={{ marginBottom: 16 }}
          />
        )}

        {status?.authenticated ? (
          <Alert
            type="success"
            showIcon
            icon={<CheckCircleFilled />}
            message="WhatsApp Connected"
            description="Your WhatsApp account is authenticated and ready to use."
          />
        ) : status?.qr_code ? (
          <div>
            <Alert
              type="info"
              showIcon
              message="Scan QR Code"
              description="Open WhatsApp on your phone, tap Menu or Settings and select Linked Devices, then point your camera at this QR code."
              style={{ marginBottom: 16 }}
            />
            <div style={{ textAlign: "center", padding: 16 }}>
              <div
                style={{
                  display: "inline-block",
                  padding: 16,
                  background: "white",
                  border: "1px solid #d9d9d9",
                  borderRadius: 4,
                  fontFamily: "monospace",
                  fontSize: 10,
                  lineHeight: 1,
                  whiteSpace: "pre",
                  wordBreak: "break-all",
                  maxWidth: 300,
                }}
              >
                {status.qr_code}
              </div>
              <div style={{ marginTop: 12, color: "#8c8c8c", fontSize: 12 }}>
                QR code refreshes automatically every 3 seconds
              </div>
              <div style={{ marginTop: 8, color: "#8c8c8c", fontSize: 11 }}>
                Note: Install a QR code generator library to display as image
              </div>
            </div>
          </div>
        ) : (
          !loading && (
            <Alert
              type="info"
              showIcon
              message="Waiting for QR Code"
              description="Starting WhatsApp client... This may take a few moments."
            />
          )
        )}
      </Card>
    </div>
  );
}
