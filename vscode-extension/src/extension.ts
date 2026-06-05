import * as vscode from 'vscode';
import { ArchitectureExplorerProvider } from './ArchitectureExplorerProvider';
import { SearchPanel } from './SearchPanel';

export function activate(context: vscode.ExtensionContext) {
    console.log('CodeAtlas extension is now active!');

    // Register Sidebar Provider
    const provider = new ArchitectureExplorerProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ArchitectureExplorerProvider.viewType, provider)
    );

    // Register Commands
    let searchCmd = vscode.commands.registerCommand('codeatlas.search', () => {
        SearchPanel.createOrShow(context.extensionUri);
    });

    let funcIntelCmd = vscode.commands.registerCommand('codeatlas.functionIntelligence', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const document = editor.document;
            const selection = editor.selection;
            const word = document.getText(document.getWordRangeAtPosition(selection.active));
            vscode.window.showInformationMessage(`CodeAtlas: Fetching intelligence for function ${word}`);
            // In full implementation, this opens a webview passing the symbol
            SearchPanel.createOrShow(context.extensionUri, { type: 'function', query: word, file: document.uri.fsPath });
        }
    });

    let classIntelCmd = vscode.commands.registerCommand('codeatlas.classIntelligence', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const document = editor.document;
            const selection = editor.selection;
            const word = document.getText(document.getWordRangeAtPosition(selection.active));
            vscode.window.showInformationMessage(`CodeAtlas: Fetching intelligence for class ${word}`);
            SearchPanel.createOrShow(context.extensionUri, { type: 'class', query: word, file: document.uri.fsPath });
        }
    });

    let fileIntelCmd = vscode.commands.registerCommand('codeatlas.fileIntelligence', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const fileName = editor.document.fileName;
            vscode.window.showInformationMessage(`CodeAtlas: Fetching intelligence for file ${fileName}`);
            SearchPanel.createOrShow(context.extensionUri, { type: 'file', query: fileName, file: fileName });
        }
    });

    context.subscriptions.push(searchCmd, funcIntelCmd, classIntelCmd, fileIntelCmd);
}

export function deactivate() {}
