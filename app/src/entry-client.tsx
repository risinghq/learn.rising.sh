import { StrictMode } from "react";
import { hydrateRoot } from "react-dom/client";

import { App } from "./App.tsx";
import type { Page } from "./model.ts";
import "./styles/app.css";

// The build writes the page's data beside the markup it rendered from it.
const data = document.getElementById("page-data");
const root = document.getElementById("root");
if (!data?.textContent || !root)
  throw new Error("The page has no data to hydrate.");

hydrateRoot(
  root,
  <StrictMode>
    <App page={JSON.parse(data.textContent) as Page} />
  </StrictMode>,
);

if ("serviceWorker" in navigator)
  addEventListener("load", () => {
    void navigator.serviceWorker.register("/sw.js");
  });
