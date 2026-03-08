import { Layout, Drawer } from "antd";
import { useEffect, useState } from "react";
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../Sidebar";
import Header from "../Header";
import ConsoleCronBubble from "../../components/ConsoleCronBubble";
import styles from "../index.module.less";
import Chat from "../../pages/Chat";
import ChannelsPage from "../../pages/Control/Channels";
import SessionsPage from "../../pages/Control/Sessions";
import CronJobsPage from "../../pages/Control/CronJobs";
import HeartbeatPage from "../../pages/Control/Heartbeat";
import AgentConfigPage from "../../pages/Agent/Config";
import SkillsPage from "../../pages/Agent/Skills";
import WorkspacePage from "../../pages/Agent/Workspace";
import MCPPage from "../../pages/Agent/MCP";
import ModelsPage from "../../pages/Settings/Models";
import EnvironmentsPage from "../../pages/Settings/Environments";

const { Content } = Layout;

const pathToKey: Record<string, string> = {
  "/chat": "chat",
  "/channels": "channels",
  "/sessions": "sessions",
  "/cron-jobs": "cron-jobs",
  "/heartbeat": "heartbeat",
  "/skills": "skills",
  "/mcp": "mcp",
  "/workspace": "workspace",
  "/agents": "agents",
  "/models": "models",
  "/environments": "environments",
  "/agent-config": "agent-config",
};

export default function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;
  const selectedKey = pathToKey[currentPath] || "chat";
  
  // Mobile drawer state
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (currentPath === "/") {
      navigate("/chat", { replace: true });
    }
  }, [currentPath, navigate]);

  // Handle window resize for mobile detection
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    if (isMobile) {
      setMobileDrawerOpen(false);
    }
  }, [currentPath, isMobile]);

  const toggleMobileDrawer = () => {
    setMobileDrawerOpen(!mobileDrawerOpen);
  };

  return (
    <Layout className={styles.mainLayout}>
      {/* Desktop Sidebar */}
      {!isMobile && <Sidebar selectedKey={selectedKey} />}
      
      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          placement="left"
          onClose={() => setMobileDrawerOpen(false)}
          open={mobileDrawerOpen}
          width={280}
          bodyStyle={{ padding: 0 }}
          className={styles.mobileDrawer}
        >
          <Sidebar selectedKey={selectedKey} />
        </Drawer>
      )}
      
      <Layout>
        <Header
          selectedKey={selectedKey}
          onMenuClick={toggleMobileDrawer}
          isMobile={isMobile}
        />
        <Content className="page-container">
          <ConsoleCronBubble />
          <div className="page-content">
            <Routes>
              <Route path="/chat" element={<Chat />} />
              <Route path="/channels" element={<ChannelsPage />} />
              <Route path="/sessions" element={<SessionsPage />} />
              <Route path="/cron-jobs" element={<CronJobsPage />} />
              <Route path="/heartbeat" element={<HeartbeatPage />} />
              <Route path="/skills" element={<SkillsPage />} />
              <Route path="/mcp" element={<MCPPage />} />
              <Route path="/workspace" element={<WorkspacePage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/environments" element={<EnvironmentsPage />} />
              <Route path="/agent-config" element={<AgentConfigPage />} />
              <Route path="/" element={<Chat />} />
            </Routes>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
