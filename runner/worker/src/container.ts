// Lo que Cloudflare publica de los tipos de instancia de Containers y de su
// tarifa. El tipo que se despliega es `INSTANCE_TYPE` de cloudflare.config.ts, y
// de él sale el precio de un segundo de instancia: no hay otra cifra que editar.
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

// Nanodólares por segundo: 0,00002 USD por vCPU, 0,0000025 por GiB de memoria y
// 0,00000007 por GB de disco.
const CPU_NANO = 20_000;
const MEMORY_NANO = 2_500;
const DISK_NANO = 70;

// Segundos sin peticiones tras los que la instancia se apaga.
export const SLEEP_AFTER_SECONDS = 60;

export interface Rates {
  // Solo mientras la instancia trabaja.
  cpu: number;
  // Memoria y disco, durante todo el tiempo que la instancia está encendida.
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

// Cloudflare cobra el tiempo en pasos de 10 ms. El redondeo es hacia arriba para
// que el contador nunca quede por debajo de la factura.
const STEP_MS = 10;

export function nanoFor(ms: number, nanoPerSecond: number): number {
  if (ms <= 0) return 0;
  return Math.ceil((Math.ceil(ms / STEP_MS) * nanoPerSecond * STEP_MS) / 1000);
}
