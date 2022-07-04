import * as vscode from 'vscode';
import { subscribeToDocumentChanges } from './diagnostics';

export function activate(context: vscode.ExtensionContext) {
	const glitchDiagnostics = vscode.languages.createDiagnosticCollection("glitch");
	context.subscriptions.push(glitchDiagnostics);
	subscribeToDocumentChanges(context, glitchDiagnostics);
}