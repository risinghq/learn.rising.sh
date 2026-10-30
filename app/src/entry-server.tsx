import { renderToString } from "react-dom/server";

import { App } from "./App.tsx";
import type { Page } from "./model.ts";

export const render = (page: Page) => renderToString(<App page={page} />);
