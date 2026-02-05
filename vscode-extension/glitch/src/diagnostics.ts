import * as cp from 'child_process';
import * as vscode from 'vscode';

const DEBOUNCE_MS = 500;

let debounceTimer: NodeJS.Timeout|undefined;
let currentProcess: cp.ChildProcess|undefined;
let glitchNotFoundShown = false;

function execGlitch(
    cmd: string, token: vscode.CancellationToken): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const process = cp.exec(cmd, (err, stdout) => {
      currentProcess = undefined;
      if (token.isCancellationRequested) {
        return resolve('');
      }
      if (err) {
        const message = err.message.toLowerCase();
        if (message.includes('not found') ||
            message.includes('not recognized') || message.includes('enoent') ||
            (err as NodeJS.ErrnoException).code === 'ENOENT' ||
            process.exitCode === 127) {
          return reject(new Error('GLITCH_NOT_FOUND'));
        }
        return reject(err);
      }
      return resolve(stdout);
    });

    currentProcess = process;

    token.onCancellationRequested(() => {
      if (process && !process.killed) {
        process.kill();
      }
    });
  });
}

async function refreshDiagnostics(
    doc: vscode.TextDocument, glitchDiagnostics: vscode.DiagnosticCollection,
    token: vscode.CancellationToken): Promise<void> {
  const configuration = vscode.workspace.getConfiguration('glitch');
  const diagnostics: vscode.Diagnostic[] = [];

  if (!configuration.get('enable')) {
    glitchDiagnostics.set(doc.uri, []);
    return;
  }

  let options = '';

  const config = configuration.get<string>('configurationPath');
  if (config && config !== '') {
    options += ` --config "${config}"`;
  }

  const tech = configuration.get<string>('tech');
  if (tech && tech !== '') {
    options += ` --tech ${tech}`;
  } else if (doc.fileName.endsWith('.yaml') || doc.fileName.endsWith('.yml')) {
    options += ' --tech ansible';
  } else if (doc.fileName.endsWith('.rb')) {
    options += ' --tech chef';
  } else if (doc.fileName.endsWith('.pp')) {
    options += ' --tech puppet';
  } else if (doc.fileName.endsWith('.tf')) {
    options += ' --tech terraform';
  } else {
    return;
  }

  const smellTypes = configuration.get<string[]>('smellTypes') || [];
  for (const smellType of smellTypes) {
    options += ` --smell-types ${smellType}`;
  }

  const cmd = `glitch lint${options} --linter "${doc.fileName}"`;

  try {
    const csv = await execGlitch(cmd, token);

    if (token.isCancellationRequested) {
      return;
    }

    glitchNotFoundShown = false;

    const lines = csv.split('\n').filter(line => line.includes(','));

    for (const line of lines) {
      const split = line.split(',', 6);
      if (split.length < 4) {
        continue;
      }

      let lineNum = parseInt(split[2], 10);
      if (isNaN(lineNum) || lineNum < 1) {
        lineNum = 1;
      }

      const range = new vscode.Range(
          lineNum - 1, 0, lineNum - 1, Number.MAX_SAFE_INTEGER);
      const diagnostic = new vscode.Diagnostic(
          range, split[0], vscode.DiagnosticSeverity.Warning);

      if (split[3]) {
        diagnostic.code = split[3];
      }

      diagnostics.push(diagnostic);
    }

    glitchDiagnostics.set(doc.uri, diagnostics);
  } catch (err) {
    if (err instanceof Error) {
      if (err.message === 'GLITCH_NOT_FOUND') {
        if (!glitchNotFoundShown) {
          glitchNotFoundShown = true;
          vscode.window.showErrorMessage(
              'GLITCH not found. Install with: pip install glitch');
        }
      } else if (err.message.includes('rego') && err.message.includes('not exist')) {
        if (!glitchNotFoundShown) {
          glitchNotFoundShown = true;
          vscode.window.showErrorMessage(
              'GLITCH: Rego query files not found. Run from GLITCH project root or reinstall.');
        }
      } else if (err.message.includes('Rego library is not available')) {
        if (!glitchNotFoundShown) {
          glitchNotFoundShown = true;
          vscode.window.showErrorMessage(
              'GLITCH: Rego shared library missing. See README for build instructions.');
        }
      } else {
        const errorParts = err.message.split('Error:');
        const errorMessage =
            errorParts.length > 1 ? errorParts[1].trim() : err.message;
        vscode.window.showErrorMessage(`GLITCH: ${errorMessage}`);
      }
    }
    glitchDiagnostics.set(doc.uri, []);
  }
}

export function subscribeToDocumentChanges(
    context: vscode.ExtensionContext,
    glitchDiagnostics: vscode.DiagnosticCollection): void {
  let cancellationTokenSource: vscode.CancellationTokenSource|undefined;

  function triggerRefresh(doc: vscode.TextDocument) {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    if (cancellationTokenSource) {
      cancellationTokenSource.cancel();
      cancellationTokenSource.dispose();
    }

    cancellationTokenSource = new vscode.CancellationTokenSource();
    const token = cancellationTokenSource.token;

    debounceTimer = setTimeout(() => {
      refreshDiagnostics(doc, glitchDiagnostics, token);
    }, DEBOUNCE_MS);
  }

  if (vscode.window.activeTextEditor) {
    triggerRefresh(vscode.window.activeTextEditor.document);
  }

  context.subscriptions.push(
      vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
          triggerRefresh(editor.document);
        }
      }));

  context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(e => {
    triggerRefresh(e.document);
  }));

  context.subscriptions.push(vscode.workspace.onDidCloseTextDocument(doc => {
    glitchDiagnostics.delete(doc.uri);
  }));

  context.subscriptions.push({
    dispose: () => {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      if (cancellationTokenSource) {
        cancellationTokenSource.cancel();
        cancellationTokenSource.dispose();
      }
      if (currentProcess && !currentProcess.killed) {
        currentProcess.kill();
      }
    }
  });
}