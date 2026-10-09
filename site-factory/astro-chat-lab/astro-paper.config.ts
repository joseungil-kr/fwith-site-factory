import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    url: process.env.ASTRO_CHAT_SITE_URL ?? "https://astro-chat-lab-qa.invalid/",
    title: "웹채팅 Astro 블로그 실험실",
    description: "웹채팅에서 구축하고 Cloudflare에 공개하는 정적 블로그 실험",
    author: "Astro 웹채팅 실험",
    profile: "",
    ogImage: "default-og.jpg",
    lang: "ko",
    timezone: "Asia/Seoul",
    dir: "ltr",
  },
  posts: {
    perPage: 4,
    perIndex: 4,
    scheduledPostMargin: 15 * 60 * 1000,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: false,
    showArchives: false,
    showBackButton: true,
    editPost: { enabled: false },
    search: false,
  },
  socials: [],
  shareLinks: [],
});