import * as vscode from "vscode";

type BackendStatus = "connected" | "disconnected";

interface AnalysisResult {
    framework?: string;
    current_version?: string;
    target_version?: string;
    migration_required?: boolean;
    issues?: string[];
}

interface AssistantResponse {
    message?: string;
    analysis?: AnalysisResult;
}

interface ProgressStep {
    label: string;
    completed?: boolean;
    in_progress?: boolean;
}

export class MigrationPanel implements vscode.WebviewViewProvider {
    public static readonly viewType = "codeshift-ai.chatView";

    private readonly viewDisposables: vscode.Disposable[] = [];
    private backendStatus: BackendStatus = "disconnected";
    private view: vscode.WebviewView | undefined;
    private welcomeSent = false;

    public constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly socket: WebSocket
    ) {
        this.setupWebSocket();
    }

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this.clearViewDisposables();
        this.view = webviewView;

        webviewView.title = "CodeShift AI";
        webviewView.description = "Migration cockpit";
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri],
        };
        webviewView.webview.html = this.getHtml(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(
            async (message: { command: string; text?: string; planId?: string }) => {
                switch (message.command) {
                    case "ready":
                        this.updateConnectionStatus(this.backendStatus === "connected");
                        this.sendWelcomeMessage();
                        break;
                    case "sendMessage":
                        await this.handleUserMessage(message.text ?? "");
                        break;
                    case "approveDeployment":
                        await this.handleApproval(message.planId ?? "");
                        break;
                    case "reviewPlan":
                        await this.handleReviewPlan(message.planId ?? "");
                        break;
                }
            },
            null,
            this.viewDisposables
        );

        webviewView.onDidDispose(
            () => {
                this.view = undefined;
                this.clearViewDisposables();
            },
            null,
            this.viewDisposables
        );
    }

    public async show() {
        await this.tryExecuteCommand(`${MigrationPanel.viewType}.focus`);
        await this.tryExecuteCommand("workbench.action.moveViewToAuxiliaryBar", MigrationPanel.viewType);
        await this.tryExecuteCommand("workbench.action.focusAuxiliaryBar");

        this.view?.show(false);
    }

    private clearViewDisposables() {
        while (this.viewDisposables.length) {
            this.viewDisposables.pop()?.dispose();
        }
    }

    private async tryExecuteCommand(command: string, ...args: unknown[]) {
        try {
            await vscode.commands.executeCommand(command, ...args);
        } catch {
            // Some workbench placement commands are version/UI-state dependent.
        }
    }

    private setupWebSocket() {
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(String(event.data)) as AssistantResponse;
                this.postToWebview({
                    command: "addAssistantMessage",
                    data,
                });
            } catch {
                this.postToWebview({
                    command: "addAssistantMessage",
                    data: { message: String(event.data) },
                });
            }
        };

        this.socket.onopen = () => {
            this.backendStatus = "connected";
            this.updateConnectionStatus(true);
        };

        this.socket.onclose = () => {
            this.backendStatus = "disconnected";
            this.updateConnectionStatus(false);
        };

        this.socket.onerror = () => {
            this.backendStatus = "disconnected";
            this.updateConnectionStatus(false);
        };
    }

    private sendWelcomeMessage() {
        if (this.welcomeSent) {
            return;
        }

        this.welcomeSent = true;
        this.postToWebview({
            command: "addAssistantMessage",
            data: {
                message: "Drop a repo goal here. I can map versions, find migration risks, and turn the upgrade into an executable plan.",
            },
        });
    }

    private async checkBackendConnection() {
        try {
            const response = await fetch("http://localhost:8000/health", {
                method: "GET",
            });

            this.backendStatus = response.ok ? "connected" : "disconnected";
            this.updateConnectionStatus(response.ok);
        } catch {
            this.backendStatus = "disconnected";
            this.updateConnectionStatus(false);
        }
    }

    private updateConnectionStatus(connected: boolean) {
        this.postToWebview({
            command: "updateStatus",
            connected,
        });
    }

    private async handleUserMessage(text: string) {
        const trimmedText = text.trim();

        if (!trimmedText) {
            return;
        }

        try {
            await this.checkBackendConnection();
            this.sendToBackend(trimmedText);
        } catch (error) {
            this.postToWebview({
                command: "addError",
                error: String(error),
            });
        }
    }

    private async handleApproval(planId: string) {
        if (!planId) {
            return;
        }

        try {
            const response = await fetch(
                "http://localhost:8000/migrations/approve",
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ planId }),
                }
            );

            const data = await response.json() as { steps: ProgressStep[] };

            this.postToWebview({
                command: "showProgress",
                steps: data.steps,
            });
        } catch (error) {
            this.postToWebview({
                command: "addError",
                error: String(error),
            });
        }
    }

    private async handleReviewPlan(planId: string) {
        console.log("Review plan:", planId);
    }

    private sendToBackend(text: string) {
        if (this.socket.readyState !== WebSocket.OPEN) {
            throw new Error("Backend chat socket is not connected.");
        }

        this.socket.send(JSON.stringify({ message: text }));
    }

    private postToWebview(message: unknown) {
        void this.view?.webview.postMessage(message);
    }

    private getHtml(webview: vscode.Webview): string {
        const nonce = this.getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';" />
    <title>CodeShift AI</title>
    <style>
        :root {
            color-scheme: light dark;
            --bg: var(--vscode-sideBar-background, var(--vscode-editor-background));
            --fg: var(--vscode-sideBar-foreground, var(--vscode-foreground));
            --muted: var(--vscode-descriptionForeground);
            --border: var(--vscode-sideBar-border, var(--vscode-panel-border));
            --input-bg: var(--vscode-input-background);
            --input-fg: var(--vscode-input-foreground);
            --button-bg: var(--vscode-button-background);
            --button-fg: var(--vscode-button-foreground);
            --button-hover: var(--vscode-button-hoverBackground);
            --focus: var(--vscode-focusBorder);
            --danger: var(--vscode-errorForeground);
            --accent: #4f8cff;
            --cyan: #20d6c7;
            --success: #33c47a;
            --warning: #f4b942;
            --surface: color-mix(in srgb, var(--bg) 84%, var(--fg) 16%);
            --surface-soft: color-mix(in srgb, var(--bg) 92%, var(--fg) 8%);
            --surface-hot: color-mix(in srgb, var(--button-bg) 22%, var(--bg) 78%);
        }

        * {
            box-sizing: border-box;
        }

        html,
        body {
            width: 100%;
            height: 100%;
            margin: 0;
            overflow: hidden;
            background: var(--bg);
            color: var(--fg);
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
        }

        button,
        textarea {
            font: inherit;
        }

        .app {
            display: grid;
            grid-template-rows: auto 1fr auto;
            height: 100%;
            min-width: 260px;
            background:
                linear-gradient(135deg, color-mix(in srgb, var(--button-bg) 18%, transparent), transparent 34%),
                radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--cyan) 16%, transparent), transparent 32%),
                var(--bg);
        }

        .hero {
            position: relative;
            padding: 14px;
            border-bottom: 1px solid var(--border);
            background: color-mix(in srgb, var(--bg) 82%, var(--button-bg) 18%);
            overflow: hidden;
        }

        .hero::before {
            content: "";
            position: absolute;
            inset: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), var(--cyan), var(--success));
        }

        .brand-row {
            display: grid;
            grid-template-columns: 38px 1fr auto;
            gap: 10px;
            align-items: center;
        }

        .logo {
            display: grid;
            place-items: center;
            width: 38px;
            height: 38px;
            border: 1px solid color-mix(in srgb, var(--accent) 55%, var(--border) 45%);
            border-radius: 10px;
            background:
                linear-gradient(135deg, color-mix(in srgb, var(--accent) 76%, black), color-mix(in srgb, var(--cyan) 58%, var(--bg)));
            color: white;
            font-weight: 800;
            letter-spacing: 0;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
        }

        .title-block {
            min-width: 0;
        }

        .title {
            margin: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 0;
        }

        .subtitle {
            margin: 2px 0 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: var(--muted);
            font-size: 11px;
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            min-height: 24px;
            padding: 4px 8px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: var(--surface-soft);
            color: var(--muted);
            font-size: 11px;
            white-space: nowrap;
        }

        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--warning);
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--warning) 22%, transparent);
        }

        .status.connected .dot {
            background: var(--success);
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--success) 22%, transparent);
        }

        .status.disconnected .dot {
            background: var(--danger);
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--danger) 18%, transparent);
        }

        .quick-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 7px;
            margin-top: 14px;
        }

        .metric {
            min-width: 0;
            padding: 9px 8px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: color-mix(in srgb, var(--surface-soft) 82%, var(--button-bg) 18%);
        }

        .metric strong {
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 12px;
        }

        .metric span {
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-top: 2px;
            color: var(--muted);
            font-size: 10px;
        }

        .messages {
            display: flex;
            flex-direction: column;
            gap: 12px;
            min-height: 0;
            padding: 14px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }

        .empty {
            display: grid;
            align-content: center;
            justify-items: center;
            gap: 14px;
            flex: 1;
            min-height: 260px;
            color: var(--muted);
            text-align: center;
        }

        .empty-badge {
            display: grid;
            place-items: center;
            width: 74px;
            height: 74px;
            border: 1px solid color-mix(in srgb, var(--accent) 44%, var(--border) 56%);
            border-radius: 18px;
            background:
                linear-gradient(145deg, color-mix(in srgb, var(--button-bg) 34%, var(--surface-soft) 66%), var(--surface));
            color: var(--button-fg);
            font-size: 24px;
            font-weight: 900;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.24);
        }

        .empty-title {
            color: var(--fg);
            font-size: 18px;
            font-weight: 800;
        }

        .empty-copy {
            max-width: 300px;
            margin: 0;
            line-height: 1.55;
        }

        .chips {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 7px;
        }

        .chip {
            min-height: 28px;
            padding: 5px 9px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: var(--surface-soft);
            color: var(--fg);
            cursor: pointer;
            font-size: 11px;
        }

        .chip:hover {
            border-color: var(--focus);
            background: var(--surface-hot);
        }

        .message {
            display: flex;
            width: 100%;
        }

        .message.assistant {
            justify-content: flex-start;
        }

        .message.user {
            justify-content: flex-end;
        }

        .bubble {
            position: relative;
            max-width: min(92%, 620px);
            padding: 11px 12px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: color-mix(in srgb, var(--surface) 78%, var(--bg) 22%);
            line-height: 1.55;
            overflow-wrap: anywhere;
            white-space: pre-wrap;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
        }

        .message.assistant .bubble {
            border-top-left-radius: 4px;
        }

        .message.user .bubble {
            border-color: color-mix(in srgb, var(--accent) 66%, var(--border) 34%);
            border-top-right-radius: 4px;
            background:
                linear-gradient(135deg, color-mix(in srgb, var(--button-bg) 88%, var(--cyan) 12%), var(--button-bg));
            color: var(--button-fg);
        }

        .card {
            display: grid;
            gap: 12px;
            min-width: min(100%, 300px);
        }

        .card-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            font-weight: 800;
        }

        .pill {
            padding: 2px 7px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--muted);
            font-size: 10px;
            font-weight: 600;
        }

        .rows {
            display: grid;
            gap: 1px;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 10px;
        }

        .row {
            display: grid;
            grid-template-columns: minmax(100px, 0.85fr) minmax(100px, 1fr);
            gap: 10px;
            padding: 9px 10px;
            background: var(--surface-soft);
        }

        .row-label {
            color: var(--muted);
        }

        .row-value {
            font-weight: 700;
            text-align: right;
        }

        .issues {
            display: grid;
            gap: 8px;
        }

        .issue {
            padding: 9px 10px;
            border: 1px solid color-mix(in srgb, var(--warning) 30%, var(--border) 70%);
            border-left: 3px solid var(--warning);
            border-radius: 8px;
            background: color-mix(in srgb, var(--warning) 10%, var(--surface-soft) 90%);
        }

        .actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .action {
            min-height: 32px;
            padding: 6px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface-soft);
            color: var(--fg);
            cursor: pointer;
            font-weight: 700;
        }

        .action.primary {
            border-color: transparent;
            background: var(--button-bg);
            color: var(--button-fg);
        }

        .action:hover {
            border-color: var(--focus);
            background: var(--button-hover);
            color: var(--button-fg);
        }

        .progress {
            display: grid;
            gap: 9px;
        }

        .step {
            display: grid;
            grid-template-columns: 20px 1fr;
            align-items: center;
            gap: 8px;
            color: var(--muted);
        }

        .step::before {
            content: "";
            width: 10px;
            height: 10px;
            border: 2px solid var(--border);
            border-radius: 50%;
        }

        .step.completed {
            color: var(--fg);
        }

        .step.completed::before {
            border-color: var(--success);
            background: var(--success);
        }

        .step.in-progress {
            color: var(--fg);
        }

        .step.in-progress::before {
            border-color: var(--warning);
            border-top-color: transparent;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }

        .error {
            padding: 10px 12px;
            border: 1px solid color-mix(in srgb, var(--danger) 58%, var(--border) 42%);
            border-left-width: 3px;
            border-radius: 9px;
            color: var(--danger);
            background: color-mix(in srgb, var(--danger) 10%, var(--surface-soft) 90%);
        }

        .composer {
            padding: 12px;
            border-top: 1px solid var(--border);
            background: color-mix(in srgb, var(--bg) 82%, var(--button-bg) 18%);
        }

        .composer-box {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 8px;
            align-items: end;
            padding: 8px;
            border: 1px solid var(--vscode-input-border, var(--border));
            border-radius: 12px;
            background: var(--input-bg);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
        }

        .composer-box:focus-within {
            border-color: var(--focus);
            outline: 1px solid var(--focus);
            outline-offset: 1px;
        }

        textarea {
            width: 100%;
            min-height: 28px;
            max-height: 148px;
            padding: 5px;
            border: 0;
            outline: 0;
            resize: none;
            background: transparent;
            color: var(--input-fg);
            line-height: 1.45;
        }

        textarea::placeholder {
            color: var(--vscode-input-placeholderForeground);
        }

        .send {
            display: grid;
            place-items: center;
            min-width: 38px;
            height: 34px;
            padding: 0 10px;
            border: 0;
            border-radius: 9px;
            background: var(--button-bg);
            color: var(--button-fg);
            cursor: pointer;
            font-size: 12px;
            font-weight: 800;
        }

        .send:hover {
            background: var(--button-hover);
        }

        .send:disabled {
            cursor: default;
            opacity: 0.52;
        }

        @media (max-width: 360px) {
            .brand-row {
                grid-template-columns: 38px 1fr;
            }

            .status {
                grid-column: 1 / -1;
                justify-self: start;
            }

            .quick-grid {
                grid-template-columns: 1fr;
            }

            .row {
                grid-template-columns: 1fr;
                gap: 2px;
            }

            .row-value {
                text-align: left;
            }
        }
    </style>
</head>
<body>
    <main class="app">
        <header class="hero">
            <div class="brand-row">
                <div class="logo" aria-hidden="true">CS</div>
                <div class="title-block">
                    <h1 class="title">CodeShift AI</h1>
                    <p class="subtitle">Migration cockpit</p>
                </div>
                <div class="status disconnected" id="status">
                    <span class="dot" aria-hidden="true"></span>
                    <span id="statusText">Connecting</span>
                </div>
            </div>
            <div class="quick-grid" aria-label="Capabilities">
                <div class="metric"><strong>Scan</strong><span>repo risk</span></div>
                <div class="metric"><strong>Plan</strong><span>upgrade path</span></div>
                <div class="metric"><strong>Ship</strong><span>guided edits</span></div>
            </div>
        </header>

        <section class="messages" id="messages" aria-live="polite">
            <div class="empty" id="emptyState">
                <div class="empty-badge" aria-hidden="true">AI</div>
                <div class="empty-title">What are we upgrading?</div>
                <p class="empty-copy">Start with a framework, version target, or migration problem. I will keep the plan tight and actionable.</p>
                <div class="chips">
                    <button class="chip" type="button" data-prompt="Analyze this workspace for migration risks">Analyze workspace</button>
                    <button class="chip" type="button" data-prompt="Create an upgrade plan for this project">Create plan</button>
                    <button class="chip" type="button" data-prompt="Find dependency upgrade blockers">Find blockers</button>
                </div>
            </div>
        </section>

        <footer class="composer">
            <div class="composer-box">
                <textarea id="messageInput" rows="1" placeholder="Ask CodeShift AI"></textarea>
                <button class="send" id="sendButton" title="Send message" aria-label="Send message">SEND</button>
            </div>
        </footer>
    </main>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const messages = document.getElementById("messages");
        const emptyState = document.getElementById("emptyState");
        const messageInput = document.getElementById("messageInput");
        const sendButton = document.getElementById("sendButton");
        const status = document.getElementById("status");
        const statusText = document.getElementById("statusText");
        const oldState = vscode.getState() || { hasMessages: false };

        let hasMessages = oldState.hasMessages;

        if (hasMessages) {
            emptyState?.remove();
        }

        vscode.postMessage({ command: "ready" });
        sendButton.disabled = true;

        for (const chip of document.querySelectorAll(".chip")) {
            chip.addEventListener("click", () => {
                messageInput.value = chip.dataset.prompt || "";
                sendButton.disabled = false;
                resizeInput();
                messageInput.focus();
            });
        }

        messageInput.addEventListener("input", () => {
            resizeInput();
            sendButton.disabled = messageInput.value.trim().length === 0;
        });

        messageInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });

        sendButton.addEventListener("click", sendMessage);

        function resizeInput() {
            messageInput.style.height = "auto";
            messageInput.style.height = Math.min(messageInput.scrollHeight, 148) + "px";
        }

        function sendMessage() {
            const text = messageInput.value.trim();

            if (!text) {
                return;
            }

            addUserMessage(text);
            messageInput.value = "";
            sendButton.disabled = true;
            resizeInput();

            vscode.postMessage({
                command: "sendMessage",
                text,
            });
        }

        function removeEmptyState() {
            if (!hasMessages) {
                emptyState?.remove();
                hasMessages = true;
                vscode.setState({ hasMessages });
            }
        }

        function appendMessage(kind, contentNode) {
            removeEmptyState();

            const message = document.createElement("div");
            message.className = "message " + kind;

            const bubble = document.createElement("div");
            bubble.className = "bubble";
            bubble.appendChild(contentNode);

            message.appendChild(bubble);
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
        }

        function addUserMessage(text) {
            appendMessage("user", document.createTextNode(text));
        }

        function addAssistantMessage(data) {
            if (!data) {
                return;
            }

            if (typeof data === "string") {
                appendMessage("assistant", document.createTextNode(data));
                return;
            }

            if (data.analysis) {
                appendMessage("assistant", buildAnalysisCard(data.analysis));
                return;
            }

            appendMessage("assistant", document.createTextNode(data.message || ""));
        }

        function buildAnalysisCard(analysis) {
            const card = document.createElement("div");
            card.className = "card";

            const title = document.createElement("div");
            title.className = "card-title";
            title.textContent = "Migration analysis";

            const badge = document.createElement("span");
            badge.className = "pill";
            badge.textContent = analysis.migration_required ? "Action needed" : "Low risk";
            title.appendChild(badge);
            card.appendChild(title);

            const rows = document.createElement("div");
            rows.className = "rows";
            addRow(rows, "Framework", analysis.framework || "Unknown");
            addRow(rows, "Current version", analysis.current_version || "Unknown");
            addRow(rows, "Target version", analysis.target_version || "Unknown");
            addRow(rows, "Migration required", analysis.migration_required ? "Yes" : "No");
            card.appendChild(rows);

            if (Array.isArray(analysis.issues) && analysis.issues.length > 0) {
                const issues = document.createElement("div");
                issues.className = "issues";

                for (const issue of analysis.issues) {
                    const item = document.createElement("div");
                    item.className = "issue";
                    item.textContent = issue;
                    issues.appendChild(item);
                }

                card.appendChild(issues);
            }

            return card;
        }

        function addRow(parent, label, value) {
            const row = document.createElement("div");
            row.className = "row";

            const labelNode = document.createElement("span");
            labelNode.className = "row-label";
            labelNode.textContent = label;

            const valueNode = document.createElement("span");
            valueNode.className = "row-value";
            valueNode.textContent = value;

            row.append(labelNode, valueNode);
            parent.appendChild(row);
        }

        function showMigrationCard(plan) {
            const card = document.createElement("div");
            card.className = "card";

            const title = document.createElement("div");
            title.className = "card-title";
            title.textContent = "Migration plan ready";
            card.appendChild(title);

            const rows = document.createElement("div");
            rows.className = "rows";
            addRow(rows, "Files modified", String(plan.files_to_modify || 0));
            addRow(rows, "Dependencies upgraded", String(plan.dependencies_upgraded || 0));
            card.appendChild(rows);

            const actions = document.createElement("div");
            actions.className = "actions";
            actions.append(
                makeActionButton("Review", () => reviewPlan(plan.id)),
                makeActionButton("Start", () => approveMigration(plan.id), true)
            );
            card.appendChild(actions);

            appendMessage("assistant", card);
        }

        function makeActionButton(label, handler, primary = false) {
            const button = document.createElement("button");
            button.className = primary ? "action primary" : "action";
            button.type = "button";
            button.textContent = label;
            button.addEventListener("click", handler);
            return button;
        }

        function showProgress(steps) {
            const wrap = document.createElement("div");
            wrap.className = "card";

            const title = document.createElement("div");
            title.className = "card-title";
            title.textContent = "Migration progress";
            wrap.appendChild(title);

            const list = document.createElement("div");
            list.className = "progress";

            for (const step of steps || []) {
                const item = document.createElement("div");
                item.className = "step " + (step.completed ? "completed" : step.in_progress ? "in-progress" : "pending");
                item.textContent = step.label;
                list.appendChild(item);
            }

            wrap.appendChild(list);
            appendMessage("assistant", wrap);
        }

        function addErrorMessage(error) {
            const errorNode = document.createElement("div");
            errorNode.className = "error";
            errorNode.textContent = "Error: " + error;
            appendMessage("assistant", errorNode);
        }

        function updateConnectionStatus(connected) {
            status.className = "status " + (connected ? "connected" : "disconnected");
            statusText.textContent = connected ? "Connected" : "Disconnected";
        }

        function approveMigration(planId) {
            vscode.postMessage({
                command: "approveDeployment",
                planId,
            });
        }

        function reviewPlan(planId) {
            vscode.postMessage({
                command: "reviewPlan",
                planId,
            });
        }

        window.addEventListener("message", (event) => {
            const message = event.data;

            switch (message.command) {
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
</html>`;
    }

    private getNonce() {
        const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        let text = "";

        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }

        return text;
    }
}
