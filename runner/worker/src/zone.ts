import { DAY_MS } from "./account.ts";

// A day is counted on the time zone's wall clock. The same calendar date has
// the same day number in every zone.

const MAX_ZONE_CHARS = 64;

const formatters = new Map<string, Intl.DateTimeFormat>();

function formatter(zone: string): Intl.DateTimeFormat {
  let format = formatters.get(zone);
  if (!format) {
    format = new Intl.DateTimeFormat("en-US", {
      timeZone: zone,
      hourCycle: "h23",
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      second: "numeric",
    });
    formatters.set(zone, format);
  }
  return format;
}

// Returns the runtime's canonical IANA name, or null for an unknown name.
export function canonicalZone(name: string): string | null {
  if (name.length === 0 || name.length > MAX_ZONE_CHARS) return null;
  try {
    return formatter(name).resolvedOptions().timeZone;
  } catch {
    return null;
  }
}

// Reads the wall clock in `zone` as a UTC timestamp.
function wallClock(ms: number, zone: string): number {
  const parts: Record<string, number> = {};
  for (const part of formatter(zone).formatToParts(ms)) {
    if (part.type !== "literal") parts[part.type] = Number(part.value);
  }
  return Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
    parts.hour,
    parts.minute,
    parts.second,
  );
}

export const localDay = (ms: number, zone: string) =>
  Math.floor(wallClock(ms, zone) / DAY_MS);

// Returns the instant at which `day` starts in `zone`. Two corrections suffice
// because the offset changes at most once around midnight.
export function startOfDay(day: number, zone: string): number {
  const wall = day * DAY_MS;
  let instant = wall;
  for (let pass = 0; pass < 2; pass++) {
    instant = wall - (wallClock(instant, zone) - instant);
  }
  return instant;
}

// Day 0 (1970-01-01) was a Thursday; Monday is 0 here.
const weekday = (day: number) => (((day + 3) % 7) + 7) % 7;

export const mondayOf = (day: number) => day - weekday(day);

export const isoDate = (day: number) =>
  new Date(day * DAY_MS).toISOString().slice(0, 10);
