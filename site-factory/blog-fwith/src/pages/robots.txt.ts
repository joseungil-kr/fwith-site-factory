import type { APIRoute } from "astro";

const getRobotsTxt = (sitemapURL: URL, indexable: boolean) =>
  indexable
    ? `User-agent: *\nAllow: /\n\nSitemap: ${sitemapURL.href}\n`
    : "User-agent: *\nDisallow: /\n";

export const GET: APIRoute = ({ site }) => {
  const sitemapURL = new URL("sitemap-index.xml", site);
  const indexable = import.meta.env.SITE_INDEXABLE === "true";
  return new Response(getRobotsTxt(sitemapURL, indexable));
};
