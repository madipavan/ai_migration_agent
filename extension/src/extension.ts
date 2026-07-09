import * as vscode from "vscode";
import { analyzeProject } from "./services/api_client";


export function activate(
    context: vscode.ExtensionContext
) {

    const disposable =
        vscode.commands.registerCommand(
            "codeshift-ai.analyze",
            async () => {

                const workspace =
                    vscode.workspace.workspaceFolders?.[0];

                if (!workspace) {
                    vscode.window.showErrorMessage(
                        "No workspace opened"
                    );
                    return;
                }


                const result =
                    await analyzeProject(
                        workspace.uri.fsPath
                    );


                vscode.window.showInformationMessage(
                    result.status
                );
            }
        );


    context.subscriptions.push(disposable);
}


export function deactivate() {}