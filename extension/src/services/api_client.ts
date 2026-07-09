import axios from "axios";


export async function analyzeProject(
    projectPath: string
) {

    const response = await axios.post(
        "http://127.0.0.1:8000/analyze",
        {
            project_path: projectPath
        }
    );

    return response.data;
}