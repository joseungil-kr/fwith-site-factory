import { cmsDate } from "../src/utils/cmsDate.ts";

const valid = [
  new Date("2026-10-09T00:00:00+09:00"),
  "2026-10-09T00:00:00+09:00",
  "2026-10-09T00:00:00.000Z",
  "2028-02-29T12:20:59+09:00",
];
const invalid = [
  "not-a-date",
  "2026-02-30T00:00:00+09:00",
  "2026-10-09",
  "2026-10-09T25:00:00+09:00",
  "2026-10-09T00:00:00",
  new Date(Number.NaN),
  "",
  null,
  1760000000000,
];
for (const entry of valid) {
  const parsed = cmsDate.safeParse(entry);
  if (!parsed.success || !(parsed.data instanceof Date) || Number.isNaN(parsed.data.getTime())) {
    throw new Error("Valid CMS datetime was rejected: " + String(entry));
  }
}
for (const entry of invalid) {
  if (cmsDate.safeParse(entry).success) {
    throw new Error("Invalid CMS datetime was accepted: " + String(entry));
  }
}
console.log(JSON.stringify({ test: "cms-dates", result: "PASS", valid: valid.length, rejected: invalid.length }));
