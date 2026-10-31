# Deploy your own copy

This guide takes a forker of the repository from nothing to a site published on
their Cloudflare account, with code execution and accounts. What each piece does
is in [runner.md](runner.md), [accounts.md](accounts.md) and
[protection.md](protection.md). Here are only steps.

Values between `< >` are yours. `<worker>` is the Worker name and `<host>` is
its domain. No secret goes in the repository or in a file you push to git.

## What you need

- A Cloudflare account on the Workers Paid plan, which Containers require.
- [mise](https://mise.jdx.dev/), [bun](https://bun.sh/) and Docker on the
  `PATH`. `cf deploy` builds the runner image on your machine, with the Python
  and uv versions that `mise.toml` pins and that
  `runner/worker/cloudflare.config.ts` reads with `mise current`.
- A Google account and a GitHub account, to register the OAuth clients.

From the repository root, install the dependencies. `mise run install` installs
those of the editor, of the shell (`app/`) and of the Worker, which brings the
`cf` CLI. During the deploy, `mise run deploy` copies KaTeX from the editor to
`site/vendor/`, writes the drill items (`mise run generate:items`), bundles the
scripts of `site/` and `editor/src/` into JavaScript
(`mise run generate:scripts`) and builds the shell: the catalog, the path pages,
the drill sessions, the privacy page and the service worker, prerendered into
`site/` (`mise run generate:app`, which needs the items). The next steps run in
`runner/worker`.

```sh
mise run install
cd runner/worker
bunx cf auth login
```

## 1. Choose the name and the domain

Both are in [`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts). The
name is `worker.name` (`duo`) and the domain is `HOME_HOST` (`learn.rising.sh`),
which the config puts in `worker.domains`. The container is `duo-runner`. Change
them to yours. `workersDev` is `false`: the Worker answers only on its domain,
not on `<worker>.<subdomain>.workers.dev`.

The domain must belong to an active zone in your Cloudflare account. On deploy,
Cloudflare creates the DNS record and the certificate. If another Worker already
serves that domain, remove it first in the dashboard (**Workers & Pages**, the
Worker, **Settings**, **Domains & Routes**): a domain serves one Worker.

## 2. Create the database

The database stores accounts, progress and attempts. Its schema is
[`src/schema.sql`](../runner/worker/src/schema.sql).

```sh
bunx cf d1 create --name qiskit-guides
```

Copy the identifier (`uuid`) from the response. The database is called
`qiskit-guides`, the name the project had before it was Rising; it is the only
place that keeps it. It must match `bindings.d1` in `cloudflare.config.ts`, and
if you choose another name, change both. Apply the schema:

```sh
bunx cf d1 query <uuid> "--sql=$(cat src/schema.sql)"
```

Write `--sql=` attached to the text. The schema starts with `--`, and without
the `=` the CLI takes it for a flag.

The file holds the whole schema, for a database that does not exist yet. A
database that is live is never recreated: it is altered in place, with the
statements of [Update a live database](#update-a-live-database) below.

## 3. Create the Turnstile widget

```sh
bunx cf turnstile widgets create --body '{"name":"duo","domains":["<host>"],"mode":"managed","region":"world"}'
```

A widget already created is valid only on the domains it lists. If you change
domain, add `<host>` to **Domains** in the Turnstile dashboard (**Turnstile**,
the widget, **Settings**) or create another widget and change
`TURNSTILE_SITE_KEY` and the secret.

Copy two values from the response:

- The site key (`sitekey`) is public. Write it in `TURNSTILE_SITE_KEY` in
  `cloudflare.config.ts`.
- The secret (`secret`) is stored without printing it. You enter it as
  `TURNSTILE_SECRET` in the temporary file of step 7.

## 4. Create the Google client

1. Open [Google Auth Platform](https://console.cloud.google.com/auth/overview)
   in a Google Cloud project, new or existing.
2. If it is the first time, click **Get started**. Enter the application name,
   your support email and, under **Audience**, choose **External**. Enter a
   contact email and accept the policy.
3. Under **Data Access**, click **Add or remove scopes** and check `openid`,
   `.../auth/userinfo.email` and `.../auth/userinfo.profile`. Save.
4. Under **Audience**, click **Publish app**. Until then only the accounts in
   the **Test users** list can sign in.
5. Under **Clients**, click **Create client**. For **Application type** choose
   **Web application** and name it.
6. Under **Authorized redirect URIs** add `https://<host>/auth/google/callback`.
   Do not add a trailing slash.
7. Click **Create**. Copy the **Client ID** and the **Client secret**: they are
   `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

What the Worker asks of each provider is in [Sign-in](accounts.md#sign-in).

## 5. Create the GitHub application

1. Open
   [Developer settings > OAuth Apps](https://github.com/settings/developers) and
   click **New OAuth App**.
2. Enter a name and, under **Homepage URL**, `https://<host>`.
3. Under **Authorization callback URL** enter
   `https://<host>/auth/github/callback`. Leave **Enable Device Flow**
   unchecked.
4. Click **Register application**. Copy the **Client ID**: it is
   `GITHUB_CLIENT_ID`.
5. Click **Generate a new client secret** and copy it: it is
   `GITHUB_CLIENT_SECRET`.

## 6. Create the push keys

The streak reminder is a web push. The Worker signs each push with a VAPID key
pair, and the browser subscribes with its public half. Make the pair once, on
your machine, from the repository root:

```sh
bun -e 'const k=await crypto.subtle.generateKey({name:"ECDSA",namedCurve:"P-256"},true,["sign"]);const j=await crypto.subtle.exportKey("jwk",k.privateKey);const b=s=>Buffer.from(s,"base64url");console.log("VAPID_PUBLIC_KEY="+Buffer.concat([Buffer.from([4]),b(j.x),b(j.y)]).toString("base64url"));console.log("VAPID_PRIVATE_KEY="+j.d)'
```

It prints two lines. The values are `VAPID_PUBLIC_KEY` (87 characters) and
`VAPID_PRIVATE_KEY` (43 characters). Keep them in a password manager: a new pair
makes every subscribed browser stop receiving pushes until its learner turns the
reminder on again.

`VAPID_SUBJECT` is a way for a push service to reach you, as `mailto:<address>`
or `https://<host>`. Use an address you read.

`PUSH_HOSTS` in `worker.env` of `cloudflare.config.ts` lists the push services a
browser may register: Google, Mozilla, Apple and Microsoft. The Worker refuses
any other address, so a learner cannot make it post to a server of their
choosing. Add a host there only for a push service you trust.

## 7. Deploy

The first deploy requires the eight secrets. `--secrets-file` reads a `.env`
that is deleted right after. Enter the Turnstile secret you copied in step 3
without showing it in the terminal. The four OAuth values are those of steps 4
and 5 and the three push values those of step 6.

```sh
mise run deploy --dry-run   # builds the image and the Worker, uploads nothing
umask 077
read -r -p 'Google Client ID: ' GOOGLE_CLIENT_ID
read -rs -p 'Google Client secret: ' GOOGLE_CLIENT_SECRET
printf '\n'
read -r -p 'GitHub Client ID: ' GITHUB_CLIENT_ID
read -rs -p 'GitHub Client secret: ' GITHUB_CLIENT_SECRET
printf '\n'
read -rs -p 'Turnstile secret: ' TURNSTILE_SECRET
printf '\n'
read -r -p 'VAPID public key: ' VAPID_PUBLIC_KEY
read -rs -p 'VAPID private key: ' VAPID_PRIVATE_KEY
printf '\n'
read -r -p 'VAPID subject (mailto:<address>): ' VAPID_SUBJECT
printf 'GOOGLE_CLIENT_ID=%s\nGOOGLE_CLIENT_SECRET=%s\nGITHUB_CLIENT_ID=%s\nGITHUB_CLIENT_SECRET=%s\nTURNSTILE_SECRET=%s\nVAPID_PUBLIC_KEY=%s\nVAPID_PRIVATE_KEY=%s\nVAPID_SUBJECT=%s\n' \
  "$GOOGLE_CLIENT_ID" "$GOOGLE_CLIENT_SECRET" "$GITHUB_CLIENT_ID" \
  "$GITHUB_CLIENT_SECRET" "$TURNSTILE_SECRET" "$VAPID_PUBLIC_KEY" \
  "$VAPID_PRIVATE_KEY" "$VAPID_SUBJECT" > "$TMPDIR/secrets.env"
mise run deploy --secrets-file "$TMPDIR/secrets.env"
rm "$TMPDIR/secrets.env"
unset GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET GITHUB_CLIENT_ID GITHUB_CLIENT_SECRET TURNSTILE_SECRET VAPID_PUBLIC_KEY VAPID_PRIVATE_KEY VAPID_SUBJECT
```

This deploys the Worker `<worker>` on `<host>`. To publish a change to the
lessons or to the Worker, run `mise run deploy` again.

## 8. Rotate a secret

After the first deploy, rotate a secret with `cf workers secrets update`. This
command does not replace the first-deploy file. Repeat the command for each name
you want to change:

```sh
read -rs -p 'Value: ' value && bunx cf workers secrets update <NAME> --worker <worker> --text "$value"
```

| `<NAME>`               | Value                        |
| ---------------------- | ---------------------------- |
| `GOOGLE_CLIENT_ID`     | The Client ID of step 4.     |
| `GOOGLE_CLIENT_SECRET` | The Client secret of step 4. |
| `GITHUB_CLIENT_ID`     | The Client ID of step 5.     |
| `GITHUB_CLIENT_SECRET` | The client secret of step 5. |
| `TURNSTILE_SECRET`     | The secret of step 3.        |
| `VAPID_PUBLIC_KEY`     | The public key of step 6.    |
| `VAPID_PRIVATE_KEY`    | The private key of step 6.   |
| `VAPID_SUBJECT`        | The contact of step 6.       |

Without `--text` the CLI sends no value. Each command creates a new version of
the Worker. While a provider's client is missing, `/auth/<provider>` answers 503
and the other one keeps working. Change `VAPID_PUBLIC_KEY` and
`VAPID_PRIVATE_KEY` together, and expect the subscribed browsers to stop
receiving pushes ([step 6](#6-create-the-push-keys)). Without the three VAPID
secrets `/api/push` answers 503 and the cron sends nothing; the rest of the site
works.

## 9. Check

```sh
curl -s https://<host>/health
curl -s https://<host>/api/me
curl -s https://<host>/ | grep -o '<title>[^<]*'
curl -s https://<host>/qiskit/ | grep -o '<title>[^<]*'
curl -s https://<host>/computational-physics/ | grep -o '<title>[^<]*'
curl -sI https://<host>/auth/google | grep -i '^location'
curl -sI https://<host>/auth/github | grep -i '^location'
```

`/health` answers 200 and `/api/me` answers `{"signedIn":false}`. `/` is the
catalog (`<title>Rising`) and `/qiskit/` and `/computational-physics/` the path
pages of the courses. The last two print an address on `accounts.google.com` and
on `github.com` with `redirect_uri=https://<host>/auth/<provider>/callback`.
That address must be the one you registered in steps 4 and 5, letter for letter.

Open any lesson page with an exercise on `<host>` and click **Ejecutar**. The
browser gets the Turnstile token, repeats the `POST /run` with that token and
must receive 200 with the program output. Then sign in with each provider and
run an exercise.

Check the push key. With a session cookie from a signed-in browser (the
`qg_auth` cookie from the browser's developer tools):

```sh
curl -s -H 'Cookie: qg_auth=<cookie>' https://<host>/api/push
```

It answers `{"key":"B...","hour":19}`, and `key` is your `VAPID_PUBLIC_KEY`.
Then open `https://<host>/amigos/` signed in and choose **Avisarme si olvido mi
racha**. Pushes reach browsers only on a real device: a push service does not
deliver to a headless browser.

The two crons are declared in `cloudflare.config.ts` and deploy with the Worker:
the hourly one sends the reminder and the daily one purges
([Retention](accounts.md#retention),
[Streak reminder](accounts.md#streak-reminder)).

## 10. Choose the maintainers

A maintainer runs code without Turnstile or a per-user limit, and spends from
the whole budget ([protection.md](protection.md#maintainers)). `MAINTAINERS` in
`worker.env` of `cloudflare.config.ts` is a list of numeric GitHub ids separated
by commas. A login does not work: it can be renamed.

To see the id of a GitHub account:

```sh
gh api users/<login> --jq .id
```

Put the ids in `MAINTAINERS` (for example `"1234,5678"`; with the list empty no
one is a maintainer) and run `mise run deploy` again. The maintainer signs in
with GitHub from the site: the Worker compares the list with the id that GitHub
returns on sign-in.

## 11. Set spend alerts

The Worker refuses to run when the estimated spend of the month reaches
`MONTHLY_BUDGET_USD`, but Cloudflare has no spend cap that stops anything. A
budget alert is a second warning, outside the Worker, and only sends an email:
it does not pause or limit usage.

1. Open the [Cloudflare dashboard](https://dash.cloudflare.com/), choose the
   account and go to **Manage Account** > **Billing** > **Billable Usage**.
2. Click **Create budget alert**.
3. Enter a name (for example `duo 1 USD`), `1` under **Budget threshold (USD)**
   and your email under **Email recipients**. Click **Save**.
4. Repeat with the name `duo 2 USD` and the threshold `2`.

The alerts measure the usage spend of the whole account, not only that of this
Worker, and exist only on pay-as-you-go accounts. If you receive the 1 USD one,
look at **Billable Usage** and at the sum of `cost_nano_usd` in the Worker logs
([protection.md](protection.md#budget)).

The 5 USD a month of the Workers Paid plan is not part of that budget: it is a
fixed fee paid apart from what the Worker spends on Containers.

## Update a live database

A change to the schema is additive, so the live database keeps its data. The
file `src/schema.sql` always holds the whole schema, and the statements that
bring a database created earlier up to date are listed here, newest last. Run
the ones your database lacks, once each, in `runner/worker`.

Streak reminder (`users.reminded_day` and `push_subscriptions`):

```sh
bunx cf d1 query <uuid> "--sql=ALTER TABLE users ADD COLUMN reminded_day INTEGER NOT NULL DEFAULT 0; CREATE TABLE push_subscriptions (endpoint TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, p256dh TEXT NOT NULL, auth TEXT NOT NULL, created_at INTEGER NOT NULL) WITHOUT ROWID; CREATE INDEX push_subscriptions_user ON push_subscriptions (user_id);"
```

Run the statements before the deploy that needs them. The new Worker reads the
new column, so a Worker deployed first fails its reminder sweep until they run.

## Variables

The non-secret variables are in `worker.env` in `cloudflare.config.ts`. To
change one, edit the file and run `mise run deploy` again. Each document gives
the variables of its part:

- Limits, budget, maintainers and Turnstile: [protection.md](protection.md).
- Session lifetime, the `/auth` limit and retention: [accounts.md](accounts.md).
