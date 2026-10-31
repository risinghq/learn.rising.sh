// The crons of cloudflare.config.ts. `scheduled` tells them apart by the string.
export const PURGE_CRON = "17 3 * * *";
// Hourly, so each learner is reached at their own local hour (src/push.ts).
export const REMINDER_CRON = "17 * * * *";
