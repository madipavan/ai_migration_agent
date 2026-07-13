from app.agents.version_discovery_agent import VersionDiscoveryAgent
from app.core import get_llm
from app.scanner.context_builder import ContextBuilder
from app.scanner.repo_scanner import RepoScanner
from app.state import AgentState


async def dependency_node(state: AgentState):
    llm = get_llm()
    print("starting repo scan....")
    repo_scanner = RepoScanner(project_path=state.project_root)
    analysis = repo_scanner.scan()
    print("building project dependency context....")
    ctx_builder = ContextBuilder(analysis=analysis)
    ctx = ctx_builder.build_dependency()
    print("starting VersionDiscoveryAgent....")
    version_dis_agent = VersionDiscoveryAgent(llm=llm)
    versions = version_dis_agent.discover(repo_context=ctx)

    return {
        "repo_analysis": analysis,
        "dependency_context": ctx,
        "repo_dependencies": versions["dependencies"],
        "framework": versions["framework"],
        "language": versions["language"],
        "runtime": versions["runtime"],
        "package_manager": versions["package_manager"],
        "build_tools": versions["build_tools"],
    }
