import * as vscode from "vscode";
import { MigrationPanel } from "./panels/MigrationPanel";


export function activate(
    context: vscode.ExtensionContext
) {

    console.log(
        "Migration Agent Activated"
    );


    const disposable =
        vscode.commands.registerCommand(
            "codeshift-ai.analyze",
            () => {

                MigrationPanel.createOrShow(
                    context.extensionUri
                );

            }
        );


    context.subscriptions.push(
        disposable
    );

}



export function deactivate() {}