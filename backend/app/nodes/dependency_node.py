from app.agents.file_classifier_agent import FileClassifierAgent
from app.agents.version_discovery_agent import VersionDiscoveryAgent
from app.core.get_llm import get_llm
from app.scanner.context_builder import ContextBuilder
from app.scanner.repo_scanner import RepoScanner
from app.services.latest_version.latest_version_service import LatestVersionService
from app.state import AgentState


async def dependency_node(state: AgentState):
    llm = get_llm()
    print("starting repo scan....")
    repo_scanner = RepoScanner(project_path=state["repo_root"])
    files = repo_scanner.scan()
    print("starting file classifier agent....")
    file_classifier = FileClassifierAgent(llm=llm)
    analysis = file_classifier.classify(files=files)
    print("building project dependency context....")
    ctx_builder = ContextBuilder(
        analysis=analysis.model_dump(), repo_root=state.get("repo_root")
    )
    ctx = ctx_builder.build_dependency()
    print("starting VersionDiscoveryAgent....")
    version_dis_agent = VersionDiscoveryAgent(llm=llm)
    versions = await version_dis_agent.discover(repo_context=ctx)

    print("Discovering latest stable versions...")
    latest_service = LatestVersionService(llm)
    versions_dict = versions.model_dump()
    print(versions_dict)
    latest_versions = await latest_service.get_latest_version(
        framework=versions_dict["framework"],
        package_manager=versions_dict["package_manager"],
    )
    return {
        "repo_analysis": analysis,
        "dependency_context": ctx,
        "repo_dependencies": versions_dict["dependencies"],
        "framework": versions_dict["framework"],
        "language": versions_dict["language"],
        "runtime": versions_dict["runtime"],
        "package_manager": versions_dict["package_manager"],
        "build_tools": versions_dict["build_tools"],
        "latest_versions": latest_versions,
    }
