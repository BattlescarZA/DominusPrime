import { Layout, Space } from "antd";
import { MenuOutlined } from "@ant-design/icons";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useTranslation } from "react-i18next";
import {
  FileTextOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  GithubOutlined,
} from "@ant-design/icons";
import { Button, Tooltip } from "@agentscope-ai/design";
import styles from "./index.module.less";

const { Header: AntHeader } = Layout;

// Navigation URLs
const NAV_URLS = {
  docs: "https://github.com/quantanova/dominus_prime_ui#readme",
  faq: "https://github.com/quantanova/dominus_prime_ui/wiki",
  changelog: "https://github.com/quantanova/dominus_prime_ui/releases",
  github: "https://github.com/quantanova/dominus_prime_ui",
} as const;

const keyToLabel: Record<string, string> = {
  chat: "nav.chat",
  channels: "nav.channels",
  sessions: "nav.sessions",
  "cron-jobs": "nav.cronJobs",
  heartbeat: "nav.heartbeat",
  skills: "nav.skills",
  mcp: "nav.mcp",
  "agent-config": "nav.agentConfig",
  workspace: "nav.workspace",
  models: "nav.models",
  environments: "nav.environments",
};

interface HeaderProps {
  selectedKey: string;
  onMenuClick?: () => void;
  isMobile?: boolean;
}

export default function Header({ selectedKey, onMenuClick, isMobile }: HeaderProps) {
  const { t } = useTranslation();

  const handleNavClick = (url: string) => {
    if (url) {
      window.open(url, "_blank");
    }
  };

  return (
    <AntHeader className={styles.header}>
      <div className={styles.headerLeft}>
        {isMobile && onMenuClick && (
          <Button
            icon={<MenuOutlined />}
            type="text"
            onClick={onMenuClick}
            className={styles.mobileMenuBtn}
          />
        )}
        <span className={styles.headerTitle}>
          {t(keyToLabel[selectedKey] || "nav.chat")}
        </span>
      </div>
      <Space size={isMobile ? "small" : "middle"} className={styles.headerRight}>
        {!isMobile && (
          <>
            <Tooltip title={t("header.changelog")}>
              <Button
                icon={<FileTextOutlined />}
                type="text"
                onClick={() => handleNavClick(NAV_URLS.changelog)}
              >
                {t("header.changelog")}
              </Button>
            </Tooltip>
            <Tooltip title={t("header.docs")}>
              <Button
                icon={<BookOutlined />}
                type="text"
                onClick={() => handleNavClick(NAV_URLS.docs)}
              >
                {t("header.docs")}
              </Button>
            </Tooltip>
            <Tooltip title={t("header.faq")}>
              <Button
                icon={<QuestionCircleOutlined />}
                type="text"
                onClick={() => handleNavClick(NAV_URLS.faq)}
              >
                {t("header.faq")}
              </Button>
            </Tooltip>
          </>
        )}
        <Tooltip title={t("header.github")}>
          <Button
            icon={<GithubOutlined />}
            type="text"
            onClick={() => handleNavClick(NAV_URLS.github)}
          >
            {!isMobile && t("header.github")}
          </Button>
        </Tooltip>
        <LanguageSwitcher />
      </Space>
    </AntHeader>
  );
}
