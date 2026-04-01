from __future__ import annotations

import argparse
import shlex
from pathlib import Path

from automation.orchestrator import BenchmarkOrchestrator, OrchestratorConfig
from automation.reporter import archive_run_artifacts, is_full_benchmark_run


def parse_csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_backend_args(value: str | None) -> list[str]:
    if not value:
        return []
    return shlex.split(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automation scaffold for isolated GitChameleon benchmark runs.")
    parser.add_argument("--benchmark-root", type=Path, default=Path.cwd())
    parser.add_argument("--dataset-path", type=Path, default=Path("dataset/dataset.jsonl"))
    parser.add_argument("--runs-root", type=Path, default=Path("runs"))
    parser.add_argument("--workspace-root", type=Path, default=Path("/tmp/gitchameleon_agent_workspaces"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--visibility-mode",
        choices=["problem-only", "visible-tests-allowed"],
        default="problem-only",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--run-id", type=str)
    prepare.add_argument("--agents", required=True, help="Comma-separated list, e.g. codex,opencode")
    prepare.add_argument("--example-ids", help="Comma-separated example ids")
    prepare.add_argument("--limit", type=int)

    run_agent = subparsers.add_parser("run-agent")
    run_agent.add_argument("--run-id", required=True)
    run_agent.add_argument("--agent", required=True, choices=["codex", "opencode"])
    run_agent.add_argument("--executable")
    run_agent.add_argument("--backend-args", help="Shell-style backend args; supports {prompt_path} etc.")
    run_agent.add_argument("--model")
    run_agent.add_argument("--provider", choices=["openai", "openrouter"])
    run_agent.add_argument("--timeout-sec", type=int, default=900)
    run_agent.add_argument("--no-stdin-prompt", action="store_true")
    run_agent.add_argument("--container-image")
    run_agent.add_argument("--container-workdir")
    run_agent.add_argument("--container-network")
    run_agent.add_argument("--container-args", help="Shell-style args passed to docker run before the image name.")

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--run-id", required=True)
    evaluate.add_argument("--agent", required=True, choices=["codex", "opencode"])
    evaluate.add_argument("--docker-image")
    evaluate.add_argument("--docker-tag")

    report = subparsers.add_parser("report")
    report.add_argument("--run-id", required=True)
    report.add_argument("--agents", required=True)

    full_run = subparsers.add_parser("full-run")
    full_run.add_argument("--run-id", type=str)
    full_run.add_argument("--agents", required=True)
    full_run.add_argument("--example-ids", help="Comma-separated example ids")
    full_run.add_argument("--limit", type=int)
    full_run.add_argument("--executable-codex")
    full_run.add_argument("--backend-args-codex")
    full_run.add_argument("--model-codex")
    full_run.add_argument("--provider-codex", choices=["openai", "openrouter"])
    full_run.add_argument("--executable-opencode")
    full_run.add_argument("--backend-args-opencode")
    full_run.add_argument("--model-opencode")
    full_run.add_argument("--timeout-sec", type=int, default=900)
    full_run.add_argument("--docker-image")
    full_run.add_argument("--docker-tag")
    full_run.add_argument("--container-image-codex")
    full_run.add_argument("--container-image-opencode")
    full_run.add_argument("--container-workdir")
    full_run.add_argument("--container-network")
    full_run.add_argument("--container-args-codex")
    full_run.add_argument("--container-args-opencode")

    return parser


def make_orchestrator(args: argparse.Namespace) -> BenchmarkOrchestrator:
    benchmark_root = args.benchmark_root.resolve()
    dataset_path = (benchmark_root / args.dataset_path).resolve() if not args.dataset_path.is_absolute() else args.dataset_path
    runs_root = (benchmark_root / args.runs_root).resolve() if not args.runs_root.is_absolute() else args.runs_root
    workspace_root = args.workspace_root.resolve() if args.workspace_root.is_absolute() else (benchmark_root / args.workspace_root).resolve()
    config = OrchestratorConfig(
        benchmark_root=benchmark_root,
        dataset_path=dataset_path,
        runs_root=runs_root,
        workspace_root=workspace_root,
        include_visible_tests=args.visibility_mode == "visible-tests-allowed",
        workers=args.workers,
    )
    return BenchmarkOrchestrator(config)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    orchestrator = make_orchestrator(args)

    if args.command == "prepare":
        agents = parse_csv_list(args.agents)
        example_ids = parse_csv_list(args.example_ids)
        run_dir = orchestrator.create_run(args.run_id, agents=agents, example_ids=example_ids, limit=args.limit)
        orchestrator.prepare(run_dir, agents=agents, example_ids=example_ids, limit=args.limit)
        print(run_dir)
        return

    if args.command == "run-agent":
        run_dir = orchestrator.config.runs_root / args.run_id
        backend_args = parse_backend_args(args.backend_args) if args.backend_args is not None else None
        solutions_path = orchestrator.run_agent(
            run_dir=run_dir,
            agent_name=args.agent,
            executable=args.executable,
            args=backend_args,
            model=args.model,
            provider=args.provider,
            timeout_sec=args.timeout_sec,
            use_stdin_prompt=False if args.no_stdin_prompt else None,
            container_image=args.container_image,
            container_workdir=args.container_workdir,
            container_network=args.container_network,
            container_args=parse_backend_args(args.container_args),
        )
        print(solutions_path)
        return

    if args.command == "evaluate":
        run_dir = orchestrator.config.runs_root / args.run_id
        eval_csv = orchestrator.evaluate_agent(
            run_dir=run_dir,
            agent_name=args.agent,
            docker_image=args.docker_image,
            docker_tag=args.docker_tag,
        )
        print(eval_csv)
        return

    if args.command == "report":
        run_dir = orchestrator.config.runs_root / args.run_id
        summaries = orchestrator.report(run_dir=run_dir, agents=parse_csv_list(args.agents))
        print(sorted(summaries))
        return

    if args.command == "full-run":
        agents = parse_csv_list(args.agents)
        example_ids = parse_csv_list(args.example_ids)
        run_dir = orchestrator.create_run(args.run_id, agents=agents, example_ids=example_ids, limit=args.limit)
        orchestrator.prepare(run_dir, agents=agents, example_ids=example_ids, limit=args.limit)
        for agent_name in agents:
            executable = getattr(args, f"executable_{agent_name}", None)
            raw_backend_args = getattr(args, f"backend_args_{agent_name}", None)
            backend_args = parse_backend_args(raw_backend_args) if raw_backend_args is not None else None
            orchestrator.run_agent(
                run_dir=run_dir,
                agent_name=agent_name,
                executable=executable,
                args=backend_args,
                model=getattr(args, f"model_{agent_name}", None),
                provider=getattr(args, f"provider_{agent_name}", None),
                timeout_sec=args.timeout_sec,
                container_image=getattr(args, f"container_image_{agent_name}", None),
                container_workdir=args.container_workdir,
                container_network=args.container_network,
                container_args=parse_backend_args(getattr(args, f"container_args_{agent_name}", None)),
            )
            orchestrator.evaluate_agent(
                run_dir=run_dir,
                agent_name=agent_name,
                docker_image=args.docker_image,
                docker_tag=args.docker_tag,
            )
        orchestrator.report(run_dir=run_dir, agents=agents)
        final_run_dir = (
            archive_run_artifacts(orchestrator.config.benchmark_root, run_dir)
            if run_dir.exists() and is_full_benchmark_run(run_dir, orchestrator.config.dataset_path)
            else run_dir
        )
        print(final_run_dir)
        return


if __name__ == "__main__":
    main()
