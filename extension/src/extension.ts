import * as vscode from "vscode";
import { MigrationPanel } from "./panels/MigrationPanel";
import { connectToWebSocket } from "./services/socket_connection";

export async function activate(
    context: vscode.ExtensionContext
) {
    console.log(
        "Migration Agent Activated"
    );

    const socket = await connectToWebSocket();
    const migrationPanel = new MigrationPanel(
        context.extensionUri,
        socket
    );

    const disposable =
        vscode.commands.registerCommand(
            "codeshift-ai.analyze",
            async () => {
                await migrationPanel.show();
            }
        );

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            MigrationPanel.viewType,
            migrationPanel,
            {
                webviewOptions: {
                    retainContextWhenHidden: true,
                },
            }
        ),
        disposable
    );
}

export function deactivate() {}
