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

export async function refreshDiagnostics(doc: vscode.TextDocument, 
		glitchDiagnostics: vscode.DiagnosticCollection) {
	const configuration = vscode.workspace.getConfiguration('glitch');
	const diagnostics: vscode.Diagnostic[] = [];

	let options = ""
	
	let config = configuration.get('configurationPath');
	console.log(config);
	if (config != "") {
		options += " --config " + config;
	}

	let tech = configuration.get('tech');
	if (tech != "") {
		options += " --tech " + tech;
		if (tech == "ansible") {
			options += " --autodetect"
		}
	} else if (doc.fileName.endsWith(".yaml") || doc.fileName.endsWith(".yml")) {
		options += " --tech ansible --autodetect"
	} else if (doc.fileName.endsWith(".rb")) {
		options += " --tech chef"
	} else if (doc.fileName.endsWith(".pp")) {
		options += " --tech puppet"
	} else {
		return;
	}

	let smells: string[] | undefined = configuration.get('smells');
	for (let i = 0; i < smells!.length; i++) {
		options += " --smells " + smells![i];
	}

	let csv;
	csv = await execShell(
		'glitch --linter ' + options + " " + doc.fileName,
	);
	
	if (csv != undefined) {
		let lines = csv.split('\n');
		lines = lines.filter(line => line.includes(','));
		for (let l = 0; l < lines.length; l++) {
			let split = lines[l].split(',', 5);

			let line = parseInt(split[2])
			if (line < 0) { line = 1; }
	
			const range = new vscode.Range(line - 1, 0, line, 0);
			diagnostics.push(
				new vscode.Diagnostic(
					range,
					split[0],
					vscode.DiagnosticSeverity.Warning
				)
			);
		}
	}

	glitchDiagnostics.set(doc.uri, diagnostics);
}

export function subscribeToDocumentChanges(context: vscode.ExtensionContext,
		glitchDiagnostics: vscode.DiagnosticCollection): void {

	if (vscode.window.activeTextEditor) {
		refreshDiagnostics(vscode.window.activeTextEditor.document, 
				glitchDiagnostics);
	}
	context.subscriptions.push(
		vscode.window.onDidChangeActiveTextEditor(editor => {
			if (editor) {
				refreshDiagnostics(editor.document, 
						glitchDiagnostics);
			}
		})
	);

	context.subscriptions.push(
		vscode.workspace.onDidChangeTextDocument(e => 
				refreshDiagnostics(e.document, glitchDiagnostics))
	);

	context.subscriptions.push(
		vscode.workspace.onDidCloseTextDocument(doc => glitchDiagnostics.delete(doc.uri))
	);
}