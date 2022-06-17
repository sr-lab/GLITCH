import * as vscode from 'vscode';

import * as cp from "child_process";

const execShell = (cmd: string) =>
    new Promise<string>((resolve, reject) => {
        cp.exec(cmd, (err, out) => {
            if (err) {
                return reject(err);
            }
            return resolve(out);
        });
    });

export async function refreshDiagnostics(doc: vscode.TextDocument, glitchDiagnostics: vscode.DiagnosticCollection) {
	const diagnostics: vscode.Diagnostic[] = [];

	let csv;
	if (doc.fileName.endsWith(".yaml") || doc.fileName.endsWith(".yml")) {
		csv = await execShell(
			'glitch --linter --tech ansible ' + doc.fileName
		);
	} else if (doc.fileName.endsWith(".rb")) {
		csv = await execShell(
			'glitch --linter --tech chef ' + doc.fileName
		);
	} else if (doc.fileName.endsWith(".pp")) {
		csv = await execShell(
			'glitch --linter --tech puppet ' + doc.fileName
		);
	}
	
	if (csv != undefined) {
		let lines = csv.split('\n');
		lines = lines.filter(line => line.includes(','));
		for (let l = 0; l < lines.length; l++) {
			let split = lines[l].split(',', 5);
	
			const range = new vscode.Range(parseInt(split[1]) - 1, 0, parseInt(split[1]), 0);
			diagnostics.push(
				new vscode.Diagnostic(
					range,
					split[4],
					vscode.DiagnosticSeverity.Warning
				)
			);
		}
	}

	glitchDiagnostics.set(doc.uri, diagnostics);
}

export function subscribeToDocumentChanges(context: vscode.ExtensionContext, glitchDiagnostics: vscode.DiagnosticCollection): void {
	if (vscode.window.activeTextEditor) {
		refreshDiagnostics(vscode.window.activeTextEditor.document, glitchDiagnostics);
	}
	context.subscriptions.push(
		vscode.window.onDidChangeActiveTextEditor(editor => {
			if (editor) {
				refreshDiagnostics(editor.document, glitchDiagnostics);
			}
		})
	);

	context.subscriptions.push(
		vscode.workspace.onDidChangeTextDocument(e => refreshDiagnostics(e.document, glitchDiagnostics))
	);

	context.subscriptions.push(
		vscode.workspace.onDidCloseTextDocument(doc => glitchDiagnostics.delete(doc.uri))
	);
}