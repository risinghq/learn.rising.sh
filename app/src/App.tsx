import { Catalog } from "./components/Catalog.tsx";
import { CoursePath } from "./components/CoursePath.tsx";
import { FriendsPage } from "./components/Friends.tsx";
import { Privacy } from "./components/Privacy.tsx";
import { SessionPage } from "./components/SessionPage.tsx";
import type { Page } from "./model.ts";

export function App({ page }: { page: Page }) {
  switch (page.kind) {
    case "catalog":
      return <Catalog page={page} />;
    case "course":
      return <CoursePath page={page} />;
    case "session":
      return <SessionPage page={page} />;
    case "friends":
      return <FriendsPage />;
    case "privacy":
      return <Privacy />;
  }
}
