import { defineAstroPaperConfig } from "./src/types/config";

export default defineAstroPaperConfig({
  site: {
    url: "https://blog.fwith.kr/",
    title: "전국 꽃배달 정보 | 꽃이랑",
    description: "지역별 근조화환, 축하화환, 꽃배달 이용 정보를 안내합니다.",
    author: "꽃이랑",
    profile: "",
    ogImage: "default-og.jpg",
    lang: "ko",
    timezone: "Asia/Seoul",
    dir: "ltr",
  },
  posts: {
    perPage: 10,
    perIndex: 10,
    scheduledPostMargin: 15 * 60 * 1000,
  },
  features: {
    lightAndDarkMode: true,
    dynamicOgImage: true,
    showArchives: false,
    showBackButton: true,
    editPost: {
      enabled: false,
      url: "",
    },
    search: "pagefind",
  },
  socials: [],
  shareLinks: [],
});
