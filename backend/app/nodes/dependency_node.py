from app.agents.file_classifier_agent import FileClassifierAgent
from app.agents.version_discovery_agent import VersionDiscoveryAgent
from app.core.get_llm import get_llm
from app.scanner.context_builder import ContextBuilder
from app.scanner.repo_scanner import RepoScanner
from app.services.technology_version.technology_version_service import (
    TechnologyVersionService,
)
from app.state import AgentState


async def dependency_node(state: AgentState):

    llm = get_llm()

    print("Starting repo scan...")
    repo_scanner = RepoScanner(project_path=state["repo_root"])
    files = repo_scanner.scan()

    print("Starting FileClassifierAgent...")
    file_classifier = FileClassifierAgent(llm=llm)
    analysis = file_classifier.classify(files=files)

    print("Building dependency context...")
    ctx_builder = ContextBuilder(
        repo_root=state["repo_root"],
        analysis=analysis.model_dump(),
    )
    ctx = ctx_builder.build_dependency()

    print("Starting VersionDiscoveryAgent...")
    version_discovery = VersionDiscoveryAgent(llm=llm)
    versions = await version_discovery.discover(repo_context=ctx)

    versions_dict = versions.model_dump()

    print("Discovering latest technology versions...")
    technology_service = TechnologyVersionService()

    latest_versions = {
        "framework": await technology_service.get_latest(versions_dict["framework"]),
        "language": await technology_service.get_latest(versions_dict["language"]),
        "runtime": await technology_service.get_latest(versions_dict["runtime"]),
    }

    return {
        "repo_analysis": analysis.model_dump(),
        "dependency_context": ctx,
        "repo_dependencies": versions_dict["dependencies"],
        "framework": versions_dict["framework"],
        "language": versions_dict["language"],
        "runtime": versions_dict["runtime"],
        "package_manager": versions_dict["package_manager"],
        "build_tools": versions_dict["build_tools"],
        "latest_versions": latest_versions,
    }
