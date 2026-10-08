import {
  defineConfig,
  envField,
  fontProviders,
  svgoOptimizer,
} from "astro/config";
import { writeFile } from "node:fs/promises";
import tailwindcss from "@tailwindcss/vite";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import { unified } from "@astrojs/markdown-remark";
import remarkToc from "remark-toc";
import remarkCollapse from "remark-collapse";
import rehypeCallouts from "rehype-callouts";
import {
  transformerNotationDiff,
  transformerNotationHighlight,
  transformerNotationWordHighlight,
} from "@shikijs/transformers";
import { transformerFileName } from "./src/utils/transformers/fileName";
import config from "./astro-paper.config";

const siteUrl = process.env.SITE_URL ?? config.site.url;

const robotsHeaders = () => ({
  name: "site-factory-noindex-headers",
  hooks: {
    "astro:build:done": async ({ dir }: { dir: URL }) => {
      const headers = process.env.SITE_INDEXABLE === "true"
        ? "/search/*\n  X-Robots-Tag: noindex, nofollow\n/archives/*\n  X-Robots-Tag: noindex, nofollow\n/404\n  X-Robots-Tag: noindex, nofollow\n"
        : "/*\n  X-Robots-Tag: noindex, nofollow\n";
      await writeFile(new URL("_headers", dir), headers);
    },
  },
});

export default defineConfig({
  site: siteUrl,
  integrations: [
    mdx(),
    sitemap({
      filter: page =>
        !page.endsWith("/search/") &&
        !page.endsWith("/404/") &&
        !page.endsWith("/404") &&
        (config.features?.showArchives !== false || !page.endsWith("/archives/")),
    }),
    robotsHeaders(),
  ],
  i18n: {
    locales: ["ko"],
    defaultLocale: "ko",
    routing: {
      prefixDefaultLocale: false,
    },
  },
  markdown: {
    processor: unified({
      remarkPlugins: [
        remarkToc,
        [remarkCollapse, { test: "Table of contents" }],
      ],
      rehypePlugins: [rehypeCallouts],
    }),
    shikiConfig: {
      themes: { light: "min-light", dark: "night-owl" },
      defaultColor: false,
      wrap: false,
      transformers: [
        transformerFileName({ style: "v2", hideDot: false }),
        transformerNotationHighlight(),
        transformerNotationWordHighlight(),
        transformerNotationDiff({ matchAlgorithm: "v3" }),
      ],
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
  fonts: [
    {
      name: "Noto Sans KR",
      cssVariable: "--font-noto-sans-kr",
      provider: fontProviders.google(),
      fallbacks: ["system-ui", "sans-serif"],
      weights: [400, 500, 700],
      styles: ["normal"],
      subsets: ["korean", "latin"],
      formats: ["woff2"],
      display: "swap",
    },
    {
      name: "Noto Sans KR",
      cssVariable: "--font-noto-sans-kr-og",
      provider: fontProviders.google(),
      weights: [400, 700],
      styles: ["normal"],
      formats: ["ttf"],
    },
  ],
  env: {
    schema: {
      PUBLIC_GOOGLE_SITE_VERIFICATION: envField.string({
        access: "public",
        context: "client",
        optional: true,
      }),
    },
  },
  experimental: {
    svgOptimizer: svgoOptimizer(),
  },
});
