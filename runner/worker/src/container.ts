// What Cloudflare publishes about the Containers instance types and their
// rate. The type that is deployed is `INSTANCE_TYPE` in cloudflare.config.ts, and
// the price of one instance second comes from it: there is no other figure to edit.
// https://developers.cloudflare.com/containers/pricing/
export const INSTANCE_TYPES = {
  lite: { vcpu: 1 / 16, gib: 0.25, gb: 2 },
  basic: { vcpu: 1 / 4, gib: 1, gb: 4 },
  "standard-1": { vcpu: 1 / 2, gib: 4, gb: 8 },
  "standard-2": { vcpu: 1, gib: 6, gb: 12 },
  "standard-3": { vcpu: 2, gib: 8, gb: 16 },
  "standard-4": { vcpu: 4, gib: 12, gb: 20 },
} as const;

export type InstanceType = keyof typeof INSTANCE_TYPES;

export const isInstanceType = (name: string): name is InstanceType =>
  Object.hasOwn(INSTANCE_TYPES, name);

// Nanodollars per second: 0.00002 USD per vCPU, 0.0000025 per GiB of memory and
// 0.00000007 per GB of disk.
const CPU_NANO = 20_000;
const MEMORY_NANO = 2_500;
const DISK_NANO = 70;

// Seconds without requests after which the instance shuts down.
export const SLEEP_AFTER_SECONDS = 60;

export interface Rates {
  // Only while the instance works.
  cpu: number;
  // Memory and disk, for as long as the instance is on.
  idle: number;
  sleepMs: number;
}

export function ratesOf(type: InstanceType): Rates {
  const spec = INSTANCE_TYPES[type];
  return {
    cpu: spec.vcpu * CPU_NANO,
    idle: spec.gib * MEMORY_NANO + spec.gb * DISK_NANO,
    sleepMs: SLEEP_AFTER_SECONDS * 1000,
  };
}

// Cloudflare bills time in steps of 10 ms. Rounding goes up so that the
// meter never falls below the bill.
const STEP_MS = 10;

export function nanoFor(ms: number, nanoPerSecond: number): number {
  if (ms <= 0) return 0;
  return Math.ceil((Math.ceil(ms / STEP_MS) * nanoPerSecond * STEP_MS) / 1000);
}
