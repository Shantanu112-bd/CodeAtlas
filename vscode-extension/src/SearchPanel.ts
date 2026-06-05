import * as vscode from 'vscode';
import axios from 'axios';

export class SearchPanel {
    public static currentPanel: SearchPanel | undefined;
    public static readonly viewType = 'codeatlasSearch';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri, initialData?: any) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        if (SearchPanel.currentPanel) {
            SearchPanel.currentPanel._panel.reveal(column);
            if (initialData) {
                SearchPanel.currentPanel._panel.webview.postMessage({ type: 'initData', data: initialData });
            }
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            SearchPanel.viewType,
            'CodeAtlas Intelligence',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [extensionUri]
            }
        );

        SearchPanel.currentPanel = new SearchPanel(panel, extensionUri, initialData);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, initialData?: any) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        this._update();

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.type) {
                    case 'search':
                        await this._handleSearch(message.query);
                        return;
                }
            },
            null,
            this._disposables
        );

        if (initialData) {
            setTimeout(() => {
                this._panel.webview.postMessage({ type: 'initData', data: initialData });
            }, 500);
        }
    }

    private async _handleSearch(query: string) {
        try {
            // Send request to CodeAtlas backend
            const response = await axios.post('http://localhost:8000/api/v1/search/hybrid', {
                repository_id: "00000000-0000-0000-0000-000000000000",
                query: query,
                limit: 10
            });
            this._panel.webview.postMessage({ type: 'searchResults', data: response.data.results });
        } catch (error) {
            console.error(error);
            this._panel.webview.postMessage({ type: 'error', message: 'Failed to connect to CodeAtlas API' });
        }
    }

    public dispose() {
        SearchPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private _update() {
        this._panel.webview.html = this._getHtmlForWebview();
    }

    private _getHtmlForWebview() {
        // Placeholder MVP Webview. 
        // Real implementation injects the Vite React build here.
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>CodeAtlas Intelligence</title>
                <style>
                    body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); }
                    input { width: 100%; padding: 10px; margin-bottom: 20px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); }
                    .result { background: var(--vscode-editor-background); border: 1px solid var(--vscode-widget-border); padding: 15px; margin-bottom: 10px; border-radius: 4px; }
                    .title { font-weight: bold; font-size: 1.1em; color: var(--vscode-textLink-foreground); }
                    .meta { font-size: 0.9em; opacity: 0.8; margin-top: 5px; }
                </style>
            </head>
            <body>
                <h1 id="header">Hybrid Semantic Search</h1>
                <input type="text" id="searchInput" placeholder="e.g. Where is authentication implemented? (Press Enter)" />
                <div id="results"></div>

                <script>
                    const vscode = acquireVsCodeApi();
                    const input = document.getElementById('searchInput');
                    const resultsDiv = document.getElementById('results');
                    const header = document.getElementById('header');

                    input.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') {
                            resultsDiv.innerHTML = 'Searching...';
                            vscode.postMessage({ type: 'search', query: input.value });
                        }
                    });

                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'searchResults':
                                resultsDiv.innerHTML = '';
                                if (!message.data || message.data.length === 0) {
                                    resultsDiv.innerHTML = 'No results found.';
                                    return;
                                }
                                message.data.forEach(res => {
                                    const div = document.createElement('div');
                                    div.className = 'result';
                                    div.innerHTML = \`<div class="title">\${res.name}</div><div class="meta">Score: \${res.score} | Intent: \${res.intent}</div>\`;
                                    resultsDiv.appendChild(div);
                                });
                                break;
                            case 'initData':
                                const init = message.data;
                                header.innerText = init.type.charAt(0).toUpperCase() + init.type.slice(1) + ' Intelligence';
                                input.value = init.query;
                                resultsDiv.innerHTML = \`Analyzing \${init.query} in \${init.file}...\`;
                                vscode.postMessage({ type: 'search', query: init.query });
                                break;
                            case 'error':
                                resultsDiv.innerHTML = \`<div style="color: var(--vscode-errorForeground)">\${message.message}</div>\`;
                                break;
                        }
                    });
                </script>
            </body>
            </html>`;
    }
}
