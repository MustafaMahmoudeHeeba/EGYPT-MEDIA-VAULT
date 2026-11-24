"""
Local integration-test / manual runner.

Thin entry point only: it creates one run (one run ID) and executes the full
pipeline. All logic lives in pipeline.egypt_media_vault.orchestration.
"""

from pipeline.egypt_media_vault.orchestration.pipeline import run_pipeline
from pipeline.egypt_media_vault.orchestration.run_context import create_pipeline_results


def main() -> bool:
    results = create_pipeline_results()

    return run_pipeline(results)


if __name__ == "__main__":
    success = main()

    if not success:
        raise SystemExit(1)
