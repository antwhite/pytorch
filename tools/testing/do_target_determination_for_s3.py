import json
import os
import pathlib
import sys

print(os.getpid(), "do_target_determination_for_s3", sys.path)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
print(os.getpid(), "do_target_determination_for_s3", sys.path)

from tools.stats.import_test_stats import (
    copy_pytest_cache,
    get_td_heuristic_historial_edited_files_json,
    get_td_heuristic_profiling_json,
    get_test_class_ratings,
    get_test_class_times,
    get_test_file_ratings,
    get_test_times,
)
from tools.stats.upload_metrics import emit_metric

from tools.testing.discover_tests import TESTS
from tools.testing.target_determination.determinator import (
    AggregatedHeuristics,
    get_prediction_confidences,
    get_test_prioritizations,
    TestPrioritizations,
)


def import_results() -> TestPrioritizations:
    if not (REPO_ROOT / ".additional_ci_files/td_results.json").exists():
        print("No TD results found")
        return TestPrioritizations([])
    with open(REPO_ROOT / ".additional_ci_files/td_results.json") as f:
        td_results = json.load(f)
        tp = TestPrioritizations.from_json(td_results)

    return tp


def main() -> None:
    selected_tests = TESTS

    aggregated_heuristics: AggregatedHeuristics = AggregatedHeuristics(
        unranked_tests=selected_tests
    )

    get_test_times()
    get_test_class_times()
    get_test_file_ratings()
    get_test_class_ratings()
    get_td_heuristic_historial_edited_files_json()
    get_td_heuristic_profiling_json()
    copy_pytest_cache()

    aggregated_heuristics = get_test_prioritizations(selected_tests)

    test_prioritizations = aggregated_heuristics.get_aggregated_priorities()

    prediction_confidences = get_prediction_confidences(selected_tests)

    if os.getenv("CI", "0") == "1":
        emit_metric(
            "td_results",
            {
                "prediction_confidences": prediction_confidences,
                "final_test_prioritizations": test_prioritizations.to_json(),
                "aggregated_heuristics": aggregated_heuristics.to_json(),
            },
        )

    with open(REPO_ROOT / "td_results.json", "w") as f:
        f.write(json.dumps(test_prioritizations.to_json()))


if __name__ == "__main__":
    main()
