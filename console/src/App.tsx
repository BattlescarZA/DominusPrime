import { createGlobalStyle } from "antd-style";
import { ConfigProvider, bailianTheme } from "@agentscope-ai/design";
import { BrowserRouter } from "react-router-dom";
import { theme } from "antd";
import MainLayout from "./layouts/MainLayout";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import "./styles/layout.css";
import "./styles/form-override.css";

const GlobalStyle = createGlobalStyle`
* {
  margin: 0;
  box-sizing: border-box;
}
`;

function AppContent() {
  const { isDarkMode } = useTheme();

  return (
    <ConfigProvider
      {...bailianTheme}
      prefix="copaw"
      prefixCls="copaw"
      theme={{
        ...bailianTheme.theme,
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: isDarkMode ? "#FFD700" : bailianTheme.theme?.token?.colorPrimary,
          colorBgBase: isDarkMode ? "#000000" : bailianTheme.theme?.token?.colorBgBase,
        },
      }}
    >
      <MainLayout />
    </ConfigProvider>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <GlobalStyle />
        <AppContent />
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
