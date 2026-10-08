import { cp, rm } from "node:fs/promises";

await rm("public/pagefind", { recursive: true, force: true });
await cp("dist/pagefind", "public/pagefind", { recursive: true });
