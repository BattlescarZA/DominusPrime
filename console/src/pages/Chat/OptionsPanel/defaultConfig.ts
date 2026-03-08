const defaultConfig = {
  theme: {
    colorPrimary: "#615CED",
    darkMode: false,
    prefix: "dominusprime",
    leftHeader: {
      logo: "",
      title: "Work with Dominus",
    },
  },
  sender: {
    attachments: false,
    maxLength: 10000,
    disclaimer: "Works for you, grows with you",
  },
  welcome: {
    greeting: "Hello, how can I help you today?",
    description:
      "I am a helpful assistant that can help you with your questions.",
    avatar: `${import.meta.env.BASE_URL}dominusprime-symbol.svg`,
    prompts: [
      {
        value: "How can you help me with my business",
      },
      {
        value: "Can you tell me what skills you have?",
      },
    ],
  },
  api: {
    baseURL: "",
    token: "",
  },
} as const;

export default defaultConfig;

export type DefaultConfig = typeof defaultConfig;
