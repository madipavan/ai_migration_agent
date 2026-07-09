import * as vscode from "vscode";

interface ChatMessage {
    type: "user" | "assistant";
    content: string;
    timestamp: number;
}

interface ProgressStep {
    label: string;
    completed: boolean;
    inProgress: boolean;
}

export class MigrationPanel {
    public static currentPanel: MigrationPanel | undefined;
    private readonly panel: vscode.WebviewPanel;
    private connectionStatus: "connected" | "disconnected" = "disconnected";

    private constructor(
        panel: vscode.WebviewPanel,
        extensionUri: vscode.Uri
    ) {
        this.panel = panel;
        this.panel.webview.html = this.getHtml();
        this.setupMessageHandlers();
        this.checkBackendConnection();
    }

    public static createOrShow(extensionUri: vscode.Uri) {
        if (MigrationPanel.currentPanel) {
            MigrationPanel.currentPanel.panel.reveal();
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            "migrationAgent",
            "CodeShift AI",
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
            }
        );

        MigrationPanel.currentPanel = new MigrationPanel(panel, extensionUri);
    }

    private setupMessageHandlers() {
        this.panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case "sendMessage":
                    await this.handleUserMessage(message.text);
                    break;
                case "approveDeployment":
                    await this.handleApproval(message.planId);
                    break;
                case "reviewPlan":
                    await this.handleReviewPlan(message.planId);
                    break;
            }
        });
    }

    private async checkBackendConnection() {
        try {
            const res = await fetch("http://localhost:8000/health", {
                method: "GET",
            });
            if (res.ok) {
                this.connectionStatus = "connected";
                this.updateConnectionStatus(true);
            }
        } catch {
            this.connectionStatus = "disconnected";
            this.updateConnectionStatus(false);
        }
    }

    private updateConnectionStatus(connected: boolean) {
        this.panel.webview.postMessage({
            command: "updateStatus",
            connected: connected,
        });
    }

    private async handleUserMessage(text: string) {
        // Add user message to UI
        this.panel.webview.postMessage({
            command: "addUserMessage",
            text: text,
        });

        try {
            const response = await this.sendToBackend(text);

            // Add assistant message
            this.panel.webview.postMessage({
                command: "addAssistantMessage",
                data: response,
            });
        } catch (error) {
            this.panel.webview.postMessage({
                command: "addError",
                error: String(error),
            });
        }
    }

    private async handleApproval(planId: string) {
        try {
            const response = await fetch(
                "http://localhost:8000/migrations/approve",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ planId: planId }),
                }
            );

            const data = await response.json() as any;

            this.panel.webview.postMessage({
                command: "showProgress",
                steps: data.steps,
            });
        } catch (error) {
            this.panel.webview.postMessage({
                command: "addError",
                error: String(error),
            });
        }
    }

    private async handleReviewPlan(planId: string) {
        // Implementation for reviewing migration plan
        console.log("Review plan:", planId);
    }

    private async sendToBackend(text: string) {
        const res = await fetch("http://localhost:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });

        if (!res.ok) {
            throw new Error(`Backend error: ${res.statusText}`);
        }

        return await res.json();
    }

    private getHtml(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CodeShift AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body {
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
            color: #e6edf3;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 13px;
            line-height: 1.5;
        }

        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100vw;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        }

        /* Header */
        .header {
            padding: 20px 16px;
            border-bottom: 1px solid #30363d;
            flex-shrink: 0;
            background: linear-gradient(180deg, rgba(22, 27, 34, 0.8) 0%, rgba(13, 17, 23, 0.6) 100%);
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .header-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 10px;
            background: linear-gradient(135deg, #58a6ff 0%, #79c0ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-subtitle {
            font-size: 12px;
            color: #8b949e;
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: #8b949e;
            margin-top: 10px;
            padding: 6px 10px;
            background: rgba(63, 75, 88, 0.4);
            border-radius: 6px;
            border: 1px solid #30363d;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3fb950 0%, #56d364 100%);
            box-shadow: 0 0 8px rgba(63, 185, 80, 0.4);
            animation: pulse 2s ease-in-out infinite;
        }

        .status-dot.disconnected {
            background: linear-gradient(135deg, #f85149 0%, #fa7a78 100%);
            box-shadow: 0 0 8px rgba(248, 81, 73, 0.4);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        /* Messages Area */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        }

        .messages-container::-webkit-scrollbar {
            width: 12px;
        }

        .messages-container::-webkit-scrollbar-track {
            background-color: transparent;
        }

        .messages-container::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #30363d 0%, #21262d 100%);
            border-radius: 6px;
            border: 3px solid transparent;
            background-clip: padding-box;
        }

        .messages-container::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #424a54 0%, #30363d 100%);
            background-clip: padding-box;
        }

        /* Message Bubbles */
        .message {
            display: flex;
            gap: 10px;
            animation: slideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(12px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message-content {
            max-width: 85%;
            padding: 12px 14px;
            border-radius: 12px;
            word-wrap: break-word;
            backdrop-filter: blur(10px);
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            color: #f0f6fc;
            border: 1px solid #3fb950;
            box-shadow: 0 8px 24px rgba(63, 185, 80, 0.2);
            font-weight: 500;
        }

        .message.assistant .message-content {
            background: linear-gradient(135deg, #1c2128 0%, #21262d 100%);
            border: 1px solid #30363d;
            color: #e6edf3;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        /* Assistant Cards */
        .assistant-card {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 14px;
            margin-top: 6px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }

        .card-title {
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 10px;
            color: #79c0ff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-section {
            margin-bottom: 12px;
            font-size: 12px;
        }

        .card-section-title {
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 6px;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.3px;
        }

        .card-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            color: #e6edf3;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
        }

        .card-row:last-child {
            border-bottom: none;
        }

        .card-row-label {
            color: #8b949e;
            font-weight: 500;
        }

        .card-row-value {
            font-weight: 700;
            background: linear-gradient(135deg, #79c0ff 0%, #58a6ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .issue-item {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 6px 0;
            color: #e6edf3;
            border-left: 3px solid #f85149;
            padding-left: 10px;
        }

        .issue-icon {
            flex-shrink: 0;
            margin-top: 2px;
            color: #f85149;
            font-weight: bold;
        }

        /* Progress UI */
        .progress-container {
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 14px;
            margin-top: 6px;
            backdrop-filter: blur(10px);
        }

        .progress-title {
            font-weight: 700;
            margin-bottom: 12px;
            color: #79c0ff;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.3px;
        }

        .progress-step {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            font-size: 12px;
            color: #e6edf3;
            font-weight: 500;
        }

        .progress-step.completed::before {
            content: "✓";
            color: #3fb950;
            font-weight: bold;
            min-width: 24px;
            font-size: 14px;
            text-shadow: 0 0 8px rgba(63, 185, 80, 0.3);
        }

        .progress-step.pending::before {
            content: "○";
            color: #6e7681;
            min-width: 24px;
            font-size: 14px;
        }

        .progress-step.in-progress::before {
            content: "⟳";
            color: #d29922;
            animation: spin 1.5s linear infinite;
            min-width: 24px;
            font-size: 14px;
            text-shadow: 0 0 8px rgba(210, 153, 34, 0.3);
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Action Buttons */
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 12px;
        }

        .button {
            flex: 1;
            padding: 10px 14px;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            text-transform: uppercase;
            letter-spacing: 0.3px;
            border: 1px solid transparent;
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }

        .button:active {
            transform: translateY(0);
        }

        .button-primary {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            color: #f0f6fc;
            box-shadow: 0 4px 12px rgba(36, 134, 54, 0.3);
        }

        .button-primary:hover {
            background: linear-gradient(135deg, #2ea043 0%, #3fb950 100%);
            box-shadow: 0 8px 20px rgba(63, 185, 80, 0.4);
        }

        .button-secondary {
            background: linear-gradient(135deg, #1f6feb 0%, #2563eb 100%);
            color: #f0f6fc;
            border: 1px solid #388bfd;
            box-shadow: 0 4px 12px rgba(56, 139, 253, 0.2);
        }

        .button-secondary:hover {
            background: linear-gradient(135deg, #388bfd 0%, #58a6ff 100%);
            border-color: #79c0ff;
            box-shadow: 0 8px 20px rgba(88, 166, 255, 0.3);
        }

        /* Input Area */
        .input-container {
            padding: 16px;
            border-top: 1px solid #30363d;
            flex-shrink: 0;
            background: linear-gradient(180deg, rgba(13, 17, 23, 0.4) 0%, rgba(22, 27, 34, 0.8) 100%);
            backdrop-filter: blur(10px);
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.2);
        }

        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }

        .textarea-wrapper {
            flex: 1;
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            border: 1.5px solid #30363d;
            border-radius: 8px;
            padding: 0 12px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .textarea-wrapper:focus-within {
            border-color: #58a6ff;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1), 0 4px 12px rgba(88, 166, 255, 0.2);
        }

        #messageInput {
            flex: 1;
            background-color: transparent;
            border: none;
            color: #e6edf3;
            outline: none;
            padding: 12px 0;
            resize: none;
            max-height: 120px;
            font-family: inherit;
            font-size: inherit;
            line-height: 1.5;
        }

        #messageInput::placeholder {
            color: #6e7681;
            font-style: italic;
        }

        .send-button {
            padding: 10px 14px;
            background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
            color: #f0f6fc;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 700;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            align-self: flex-end;
            margin-bottom: 2px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 44px;
            min-height: 44px;
            box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3);
        }

        .send-button:hover {
            background: linear-gradient(135deg, #388bfd 0%, #58a6ff 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(88, 166, 255, 0.4);
        }

        .send-button:active {
            transform: translateY(0);
        }

        /* Empty State */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #8b949e;
            text-align: center;
            padding: 40px 20px;
        }

        .empty-state-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #58a6ff 0%, #79c0ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .empty-state-text {
            font-size: 13px;
            max-width: 240px;
            line-height: 1.6;
        }

        /* Error Message */
        .error-message {
            background: linear-gradient(135deg, rgba(248, 81, 73, 0.1) 0%, rgba(248, 81, 73, 0.05) 100%);
            border: 1px solid #f85149;
            border-left: 4px solid #f85149;
            border-radius: 8px;
            padding: 12px 14px;
            color: #f85149;
            font-size: 12px;
            margin-top: 6px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(248, 81, 73, 0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">
                🤖 CodeShift AI
            </div>
            <div class="header-subtitle">
                AI Migration Assistant for Framework Upgrades
            </div>
            <div class="status-indicator">
                <div class="status-dot connected" id="statusDot"></div>
                <span id="statusText">Connecting to Backend...</span>
            </div>
        </div>

        <div class="messages-container" id="messagesContainer">
            <div class="empty-state">
                <div class="empty-state-title">Welcome to CodeShift AI</div>
                <div class="empty-state-text">
                    Intelligent project analysis and migration assistance. Ask me about upgrading your framework to the latest version.
                </div>
            </div>
        </div>

        <div class="input-container">
            <div class="input-wrapper">
                <div class="textarea-wrapper">
                    <textarea
                        id="messageInput"
                        placeholder="Ask CodeShift AI about migrating your project..."
                        rows="1"
                    ></textarea>
                </div>
                <button class="send-button" id="sendButton" title="Send message (Enter)">↑</button>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const messagesContainer = document.getElementById("messagesContainer");
        const messageInput = document.getElementById("messageInput");
        const sendButton = document.getElementById("sendButton");
        const statusDot = document.getElementById("statusDot");
        const statusText = document.getElementById("statusText");

        let hasMessages = false;

        // Auto-resize textarea
        messageInput.addEventListener("input", () => {
            messageInput.style.height = "auto";
            messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
        });

        // Send on Enter, newline on Shift+Enter
        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        sendButton.addEventListener("click", sendMessage);

        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text) return;

            addUserMessage(text);
            messageInput.value = "";
            messageInput.style.height = "auto";

            vscode.postMessage({
                command: "sendMessage",
                text: text,
            });
        }

        function removeEmptyState() {
            if (!hasMessages) {
                messagesContainer.innerHTML = "";
                hasMessages = true;
            }
        }

        function addUserMessage(text) {
            removeEmptyState();
            const messageDiv = document.createElement("div");
            messageDiv.className = "message user";
            messageDiv.innerHTML = \`
                <div class="message-content">\${escapeHtml(text)}</div>
            \`;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addAssistantMessage(data) {
            removeEmptyState();
            const messageDiv = document.createElement("div");
            messageDiv.className = "message assistant";

            let content = \`<div class="message-content">\`;

            if (typeof data === "string") {
                content += \`<div>\${escapeHtml(data)}</div>\`;
            } else if (data.analysis) {
                content += buildAnalysisCard(data.analysis);
            } else if (data.message) {
                content += \`<div>\${escapeHtml(data.message)}</div>\`;
            }

            content += "</div>";
            messageDiv.innerHTML = content;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function buildAnalysisCard(analysis) {
            return \`
                <div class="assistant-card">
                    <div class="card-title">📊 Migration Analysis</div>
                    
                    <div class="card-section">
                        <div class="card-row">
                            <span class="card-row-label">Framework</span>
                            <span class="card-row-value">\${escapeHtml(analysis.framework || "Unknown")}</span>
                        </div>
                        <div class="card-row">
                            <span class="card-row-label">Current Version</span>
                            <span class="card-row-value">\${escapeHtml(analysis.current_version || "Unknown")}</span>
                        </div>
                        <div class="card-row">
                            <span class="card-row-label">Target Version</span>
                            <span class="card-row-value">\${escapeHtml(analysis.target_version || "Unknown")}</span>
                        </div>
                        <div class="card-row">
                            <span class="card-row-label">Migration Required</span>
                            <span class="card-row-value">\${analysis.migration_required ? "✓ YES" : "○ NO"}</span>
                        </div>
                    </div>

                    \${analysis.issues && analysis.issues.length > 0 ? \`
                        <div class="card-section">
                            <div class="card-section-title">⚠ Issues Found</div>
                            \${analysis.issues.map(issue => \`
                                <div class="issue-item">
                                    <span class="issue-icon">⚠</span>
                                    <span>\${escapeHtml(issue)}</span>
                                </div>
                            \`).join("")}
                        </div>
                    \` : ""}
                </div>
            \`;
        }

        function showMigrationCard(plan) {
            removeEmptyState();
            const cardDiv = document.createElement("div");
            cardDiv.className = "message assistant";
            cardDiv.innerHTML = \`
                <div class="message-content">
                    <div class="assistant-card">
                        <div class="card-title">✅ Migration Plan Ready</div>
                        
                        <div class="card-section">
                            <div class="card-section-title">📋 Changes</div>
                            <div class="card-row">
                                <span class="card-row-label">Files Modified</span>
                                <span class="card-row-value">\${plan.files_to_modify} files</span>
                            </div>
                            <div class="card-row">
                                <span class="card-row-label">Dependencies Upgraded</span>
                                <span class="card-row-value">\${plan.dependencies_upgraded} dependencies</span>
                            </div>
                        </div>

                        <div class="button-group">
                            <button class="button button-secondary" onclick="reviewPlan('\${plan.id}')">
                                📄 Review Plan
                            </button>
                            <button class="button button-primary" onclick="approveMigration('\${plan.id}')">
                                ▶ Start Migration
                            </button>
                        </div>
                    </div>
                </div>
            \`;
            messagesContainer.appendChild(cardDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showProgress(steps) {
            removeEmptyState();
            const progressDiv = document.createElement("div");
            progressDiv.className = "message assistant";
            progressDiv.innerHTML = \`
                <div class="message-content">
                    <div class="progress-container">
                        <div class="progress-title">🔄 Migration in Progress</div>
                        \${steps.map(step => \`
                            <div class="progress-step \${step.completed ? "completed" : step.in_progress ? "in-progress" : "pending"}">
                                \${step.label}
                            </div>
                        \`).join("")}
                    </div>
                </div>
            \`;
            messagesContainer.appendChild(progressDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function addErrorMessage(error) {
            removeEmptyState();
            const errorDiv = document.createElement("div");
            errorDiv.className = "message assistant";
            errorDiv.innerHTML = \`
                <div class="message-content">
                    <div class="error-message">
                        ❌ Error: \${escapeHtml(error)}
                    </div>
                </div>
            \`;
            messagesContainer.appendChild(errorDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function updateConnectionStatus(connected) {
            if (connected) {
                statusDot.className = "status-dot connected";
                statusText.textContent = "● Backend Connected";
            } else {
                statusDot.className = "status-dot disconnected";
                statusText.textContent = "● Backend Disconnected";
            }
        }

        function approveMigration(planId) {
            vscode.postMessage({
                command: "approveDeployment",
                planId: planId,
            });
        }

        function reviewPlan(planId) {
            vscode.postMessage({
                command: "reviewPlan",
                planId: planId,
            });
        }

        function escapeHtml(text) {
            const map = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;",
            };
            return text.replace(/[&<>"']/g, (m) => map[m]);
        }

        // Message handling
        window.addEventListener("message", (event) => {
            const message = event.data;
            switch (message.command) {
                case "addUserMessage":
                    addUserMessage(message.text);
                    break;
                case "addAssistantMessage":
                    addAssistantMessage(message.data);
                    break;
                case "showMigrationCard":
                    showMigrationCard(message.plan);
                    break;
                case "showProgress":
                    showProgress(message.steps);
                    break;
                case "addError":
                    addErrorMessage(message.error);
                    break;
                case "updateStatus":
                    updateConnectionStatus(message.connected);
                    break;
            }
        });
    </script>
</body>
</html>
        `;
    }
}
