const READY_TIMEOUT_MS = 5000;

export type Reminders =
  /** The browser cannot receive pushes, as iOS Safari outside an installed app. */
  | "unsupported"
  /** The learner refused notifications for this site. */
  | "blocked"
  | "off"
  | "on";

export const supported = () =>
  "serviceWorker" in navigator &&
  "PushManager" in window &&
  "Notification" in window;

async function registration(): Promise<ServiceWorkerRegistration> {
  const found = await Promise.race([
    navigator.serviceWorker.ready,
    new Promise<undefined>((done) => setTimeout(done, READY_TIMEOUT_MS)),
  ]);
  if (!found) throw new Error("service worker");
  return found;
}

/** Whether this browser receives the reminder now. */
export async function current(): Promise<Reminders> {
  if (!supported()) return "unsupported";
  if (Notification.permission === "denied") return "blocked";
  const subscription = await (
    await registration()
  ).pushManager.getSubscription();
  return subscription && Notification.permission === "granted" ? "on" : "off";
}

const bytes = (key: string) =>
  Uint8Array.from(atob(key.replaceAll("-", "+").replaceAll("_", "/")), (c) =>
    c.charCodeAt(0),
  );

/** Reads the public key and the hour of the reminder, or null when the deployment has none. */
export async function settings(): Promise<{
  key: string;
  hour: number;
} | null> {
  const resp = await QGAccount.request("GET", "/api/push");
  return resp.ok
    ? ((await resp.json()) as { key: string; hour: number })
    : null;
}

/**
 * Asks for permission, subscribes this browser and registers it with the account. It must run
 * from a click, since browsers refuse the permission prompt otherwise.
 */
export async function enable(key: string): Promise<"on" | "blocked"> {
  if ((await Notification.requestPermission()) !== "granted") return "blocked";
  const worker = await registration();
  const subscription =
    (await worker.pushManager.getSubscription()) ??
    (await worker.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: bytes(key),
    }));
  const { endpoint, keys } = subscription.toJSON();
  const resp = await QGAccount.request("POST", "/api/push", { endpoint, keys });
  if (!resp.ok) {
    await subscription.unsubscribe();
    throw new Error(String(resp.status));
  }
  return "on";
}

/** Forgets this browser, in the account and in the browser. */
export async function disable(): Promise<void> {
  const subscription = await (
    await registration()
  ).pushManager.getSubscription();
  if (!subscription) return;
  const resp = await QGAccount.request("DELETE", "/api/push", {
    endpoint: subscription.endpoint,
  });
  if (!resp.ok) throw new Error(String(resp.status));
  await subscription.unsubscribe();
}
