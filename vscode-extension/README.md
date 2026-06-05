# CodeAtlas VS Code Extension

Bring repository intelligence directly into your editor workflow. The CodeAtlas extension connects to the CodeAtlas backend to provide deep, graph-aware insights into your codebase without ever leaving VS Code.

## Features

### 🔍 Hybrid Semantic Search
Press `Cmd+Shift+P` -> `CodeAtlas: Search` to ask natural language questions about your repository. The search engine combines Vector Embeddings with Graph Context to deliver highly accurate answers (e.g., "Where is authentication implemented?").

### 🧠 Symbol Intelligence (Right-Click)
Context menus available directly in your editor:
- **Function Intelligence**: Right-click any function to view its Call Graph, Impact Radius, and Dependencies.
- **Class Intelligence**: Right-click any class to view its Inheritance Tree and consumers.
- **File Intelligence**: Right-click any file to assess Blast Radius before refactoring or deleting.

### 📐 Architecture Explorer Sidebar
Click the CodeAtlas icon in the Activity Bar to view repository health stats, dependencies, and dynamically generated architecture diagrams.

## Setup

1. Install the extension.
2. Ensure the CodeAtlas backend is running locally (`http://localhost:8000`).
3. Open a repository indexed by CodeAtlas.

## Requirements

- VS Code 1.80.0+
- CodeAtlas Backend API

## License

MIT
