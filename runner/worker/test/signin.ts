import type { Harness } from "./harness.ts";
import type { ProviderName } from "./provider.ts";

export const cookieOf = (setCookie: string[], name: string) =>
  setCookie
    .map((line) => line.split(";")[0])
    .find((pair) => pair.startsWith(`${name}=`));

export const setCookies = (headers: Headers) => headers.getSetCookie();

// The learner clicks «entrar», approves at the provider and the browser returns.
export async function begin(
  h: Harness,
  provider: ProviderName,
  query = "",
  ip?: string,
) {
  const start = await h.request("GET", `/auth/${provider}${query}`, { ip });
  const location = start.headers.get("location");
  const flow = cookieOf(setCookies(start.headers), "qg_oauth");
  return { start, location, flow };
}

export async function signIn(
  h: Harness,
  provider: ProviderName,
  subject: string,
  query = "?return=/lesson.html",
  ip?: string,
) {
  const { location, flow } = await begin(h, provider, query, ip);
  const code = h.provider.consent(location!, subject);
  const state = new URL(location!).searchParams.get("state")!;
  const back = await h.request(
    "GET",
    `/auth/${provider}/callback?code=${code}&state=${state}`,
    {
      ip,
      headers: { cookie: flow! },
    },
  );
  const cookie = cookieOf(setCookies(back.headers), "qg_auth");
  return { back, cookie, code, state, flow: flow! };
}
