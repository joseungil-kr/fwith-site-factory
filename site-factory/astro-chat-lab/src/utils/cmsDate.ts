import { z } from "astro/zod";

/**
 * AstroPaper's original unquoted YAML timestamps are parsed as Date values.
 * Decap's datetime widget may serialize an ISO-8601 string with an explicit offset.
 * Only these two representations are accepted; invalid calendars and naive
 * timezone-free strings remain schema errors.
 */
export const cmsDate = z.union([
  z.date(),
  z.iso.datetime({ offset: true }).transform(value => new Date(value)),
]);
