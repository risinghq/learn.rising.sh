import { Check, Copy } from "lucide-react";
import { useState } from "react";

const REPOSITORY = "https://github.com/risinghq/learn.rising.sh";

export function Command({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () =>
    navigator.clipboard?.writeText(command).then(() => setCopied(true));
  const Icon = copied ? Check : Copy;
  return (
    <div className="cmd">
      <code>{command}</code>
      <button type="button" className="btn" onClick={copy}>
        <Icon aria-hidden="true" />
        <span aria-live="polite">{copied ? "Copiado" : "Copiar"}</span>
      </button>
    </div>
  );
}

export function NotebookHelp() {
  return (
    <p className="help">
      Cómo ejecutar los cuadernos: clona el{" "}
      <a href={REPOSITORY} target="_blank" rel="noopener">
        repositorio
      </a>{" "}
      y sigue «Instalar» en su README.
    </p>
  );
}
