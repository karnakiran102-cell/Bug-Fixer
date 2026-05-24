"use client";

import Editor from "@monaco-editor/react";
import { useEditorStore } from "@/store/useEditorStore";

const DEFAULT_CODE = `// Nexus AI - Agent Core Logic
import { Analyzer } from "@nexus/analyzer";

export async function executeAgentTask(taskId: string) {
  console.log(\`Initializing AI analysis for task: \${taskId}\`);
  
  const analyzer = new Analyzer();
  const result = await analyzer.scanDependencies();
  
  return { status: 200, output: result };
}`;

export default function CodeEditor() {
  const code = useEditorStore((state: any) => state.code);
  const setCode = useEditorStore((state: any) => state.setCode);

  const handleEditorWillMount = (monaco: any) => {
    monaco.editor.defineTheme("nexus-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#060816",
        "editor.lineHighlightBackground": "#101425",
        "editorCursor.foreground": "#7C3AED",
      },
    });
  };

  return (
    <Editor
      height="100%"
      defaultLanguage="typescript"
      theme="nexus-dark"
      value={code || DEFAULT_CODE}
      onChange={(value) => setCode(value || "")}
      beforeMount={handleEditorWillMount}
      options={{ minimap: { enabled: false }, fontSize: 13, fontFamily: "'Geist Mono', monospace", padding: { top: 16 }, scrollBeyondLastLine: false, smoothScrolling: true, cursorBlinking: "smooth", cursorSmoothCaretAnimation: "on", formatOnPaste: true }}
    />
  );
}