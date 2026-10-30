// Lesson text with `code`, **bold** and $math$. KaTeX is large, so it loads only when a text has math.
import { useEffect, useState } from "react";

interface Katex {
  renderToString: (tex: string, options: { throwOnError: boolean }) => string;
}
declare global {
  interface Window {
    katex?: Katex;
  }
}

let loading: Promise<Katex> | undefined;
function loadKatex(): Promise<Katex> {
  loading ??= new Promise((resolve, reject) => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "/vendor/katex/katex.min.css";
    const script = document.createElement("script");
    script.src = "/vendor/katex/katex.min.js";
    script.addEventListener("load", () =>
      window.katex ? resolve(window.katex) : reject(new Error("katex")),
    );
    script.addEventListener("error", () => reject(new Error("katex")));
    document.head.append(css, script);
  });
  return loading;
}

function useKatex(needed: boolean) {
  const [katex, setKatex] = useState<Katex | undefined>();
  useEffect(() => {
    if (needed && !katex)
      (window.katex ? Promise.resolve(window.katex) : loadKatex()).then(
        setKatex,
        () => undefined,
      );
  }, [needed, katex]);
  return katex;
}

const TOKEN = /(\$[^$]+\$|`[^`]+`|\*\*[^*]+\*\*)/;
const isMath = (part: string) =>
  part.length > 2 && part.startsWith("$") && part.endsWith("$");

export function Rich({ text }: { text: string }) {
  const parts = text.split(TOKEN);
  const katex = useKatex(parts.some(isMath));
  return (
    <>
      {parts.map((part, k) => {
        if (isMath(part)) {
          const tex = part.slice(1, -1);
          return katex ? (
            <span
              key={k}
              dangerouslySetInnerHTML={{
                __html: katex.renderToString(tex, { throwOnError: false }),
              }}
            />
          ) : (
            <span key={k}>{tex}</span>
          );
        }
        if (part.startsWith("`") && part.length > 2)
          return <code key={k}>{part.slice(1, -1)}</code>;
        if (part.startsWith("**") && part.length > 4)
          return <b key={k}>{part.slice(2, -2)}</b>;
        return part;
      })}
    </>
  );
}
