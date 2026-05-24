"use client";

import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "xterm";
import { FitAddon } from "@xterm/addon-fit";
// @ts-ignore
import "xterm/css/xterm.css";

export default function Terminal() {
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      theme: {
        background: "#0A0D1A",
        foreground: "#F8FAFC",
        cursor: "#7C3AED",
        selectionBackground: "rgba(124, 58, 237, 0.4)",
        black: "#060816",
      },
      fontFamily: "'Geist Mono', 'Inter', monospace",
      fontSize: 13,
      cursorBlink: true,
      allowProposedApi: true,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);
    
    // Slight delay to ensure parent container has painted before fitting
    setTimeout(() => fitAddon.fit(), 10);

    term.writeln("\x1b[1;35mNexus AI\x1b[0m Subsystem Console initialized.");
    term.writeln("Awaiting live agent streaming outputs...");
    term.write("\r\n\x1b[1;32mroot@nexus-ai\x1b[0m:~/project$ ");

    term.onKey(({ key, domEvent }) => {
      const ev = domEvent;
      const printable = !ev.altKey && !ev.ctrlKey && !ev.metaKey;

      if (ev.keyCode === 13) term.write("\r\n\x1b[1;32mroot@nexus-ai\x1b[0m:~/project$ ");
      else if (ev.keyCode === 8) term.write("\b \b");
      else if (printable) term.write(key);
    });

    const handleResize = () => fitAddon.fit();
    window.addEventListener("resize", handleResize);

    return () => { window.removeEventListener("resize", handleResize); term.dispose(); };
  }, []);

  return <div ref={terminalRef} className="w-full h-full" />;
}