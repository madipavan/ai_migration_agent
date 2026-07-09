import * as vscode from "vscode";
import { MigrationPanel } from "./panels/MigrationPanel";
import { connectToWebSocket } from "./services/socket_connection";


export async function activate(
    context: vscode.ExtensionContext
) {

    console.log(
        "Migration Agent Activated"
    );
    const socket = await connectToWebSocket()

    const disposable =
        vscode.commands.registerCommand(
            "codeshift-ai.analyze",
            () => {

                MigrationPanel.createOrShow(
                    context.extensionUri,
                    socket
                );

            }
        );


    context.subscriptions.push(
        disposable
    );

}



export function deactivate() {}