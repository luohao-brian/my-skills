import contextlib
import datetime as dt
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "open_source_updates.py"
SPEC = importlib.util.spec_from_file_location("open_source_updates", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def model_row(model_id, **overrides):
    row = {
        "id": model_id,
        "createdAt": "2026-07-01T00:00:00.000Z",
        "lastModified": "2026-07-01T00:00:00.000Z",
        "pipeline_tag": "text-generation",
        "trendingScore": 20,
        "downloads": 5_000,
        "likes": 30,
        "tags": [],
        "cardData": {},
    }
    row.update(overrides)
    return row


class CurrentHotSignalTests(unittest.TestCase):
    def test_current_run_can_keep_persistent_hot_model(self):
        row = model_row("community/model")
        signal = MODULE.local_signal(
            row,
            dt.date(2026, 7, 27),
            dt.date(2026, 8, 2),
            include_persistent_hot=True,
        )
        self.assertEqual(signal, ("trending-observed", "2026-08-02"))

    def test_historical_run_does_not_use_current_hot_signal(self):
        row = model_row("community/model")
        signal = MODULE.local_signal(
            row,
            dt.date(2026, 7, 27),
            dt.date(2026, 8, 2),
            include_persistent_hot=False,
        )
        self.assertIsNone(signal)

    def test_historical_registered_local_uses_priority_not_current_heat(self):
        hot_row = model_row("community/model", trendingScore=100)
        cold_row = model_row("community/model", trendingScore=0, downloads=0, likes=0)
        event = ("repository-updated", "2026-08-02")
        self.assertEqual(
            MODULE.registered_local_selection(
                hot_row,
                event,
                priority=True,
                include_current_hot=False,
            ),
            ["priority"],
        )
        self.assertEqual(
            MODULE.registered_local_selection(
                cold_row,
                event,
                priority=True,
                include_current_hot=False,
            ),
            ["priority"],
        )


class GlobalDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "families": [{"id": "official", "owner": "Official"}],
            "flagship_models": {},
            "local_versions": [],
            "local_roots": [],
            "local_publishers": [],
            "model_overrides": {},
        }
        self.start = dt.date(2026, 7, 27)
        self.end = dt.date(2026, 8, 2)

    def test_unknown_owner_hot_model_enters_discovery(self):
        row = model_row(
            "NewLab/full-model",
            createdAt="2026-07-30T00:00:00.000Z",
            lastModified="2026-07-30T00:00:00.000Z",
        )
        items = MODULE.model_discovery_items(
            [row], set(), self.registry, self.start, self.end
        )
        self.assertEqual([item["title"] for item in items], ["NewLab/full-model"])
        self.assertIn("global-discovery", items[0]["metadata"]["selection"])
        self.assertEqual(items[0]["metadata"]["publisher_tier"], "unregistered")

    def test_unknown_owner_cold_model_is_ignored(self):
        row = model_row(
            "NewLab/cold-model",
            createdAt="2026-07-30T00:00:00.000Z",
            lastModified="2026-07-30T00:00:00.000Z",
            trendingScore=2,
            downloads=100,
            likes=1,
        )
        items = MODULE.model_discovery_items(
            [row], set(), self.registry, self.start, self.end
        )
        self.assertEqual(items, [])

    def test_historical_run_ignores_unknown_owner_current_heat(self):
        row = model_row(
            "NewLab/hot-today",
            createdAt="2026-07-30T00:00:00.000Z",
            lastModified="2026-07-30T00:00:00.000Z",
            trendingScore=100,
            downloads=1_000_000,
            likes=1_000,
        )
        items = MODULE.model_discovery_items(
            [row],
            set(),
            self.registry,
            self.start,
            self.end,
            allow_unregistered_hot=False,
        )
        self.assertEqual(items, [])

    def test_unknown_owner_derivative_is_left_for_local_group(self):
        row = model_row(
            "NewLab/quantized-model",
            createdAt="2026-07-30T00:00:00.000Z",
            lastModified="2026-07-30T00:00:00.000Z",
            tags=["base_model:quantized:Official/base"],
            cardData={"base_model": "Official/base"},
        )
        items = MODULE.model_discovery_items(
            [row], set(), self.registry, self.start, self.end
        )
        self.assertEqual(items, [])


class ArchitectureFacetTests(unittest.TestCase):
    def test_arbitrary_config_does_not_imply_dense_architecture(self):
        row = model_row("community/model", config={"model_type": "custom"})
        self.assertEqual(MODULE.architecture_facet(row), "unknown")

    def test_structured_expert_count_identifies_moe(self):
        row = model_row("community/model", config={"num_experts": 256})
        self.assertEqual(MODULE.architecture_facet(row), "moe")

    def test_architecture_classes_are_preserved_without_inference(self):
        row = model_row(
            "community/model",
            config={"architectures": ["ExampleForConditionalGeneration"]},
        )
        self.assertEqual(
            MODULE.architecture_classes(row),
            ["ExampleForConditionalGeneration"],
        )

    def test_composed_pipeline_is_parsed_without_registry_entry(self):
        pipeline = "image-text-to-audio-video"
        self.assertNotIn(pipeline, MODULE.PIPELINE_MODALITIES)
        row = model_row("community/video", pipeline_tag=pipeline)
        evidence = MODULE.modality_evidence(row)
        self.assertEqual(MODULE.model_role(row), "video-generation")
        self.assertEqual(evidence["input"], ["image", "text"])
        self.assertEqual(evidence["output"], ["audio", "video"])
        self.assertEqual(
            evidence["signals"],
            [{"source": "pipeline_tag", "value": pipeline}],
        )
        metadata = MODULE.model_metadata(
            row,
            {"track": "discovery", "role": "video-generation"},
            {"families": [], "model_overrides": {}, "local_publishers": []},
        )
        self.assertEqual(metadata["modalities"], {"input": ["image", "text"], "output": ["audio", "video"]})
        self.assertEqual(metadata["role_evidence"]["task_signals"], evidence["signals"])

    def test_task_tags_can_fill_missing_pipeline_signal(self):
        row = model_row(
            "community/video",
            pipeline_tag="",
            tags=["multimodal", "text-to-audio-video"],
        )
        self.assertEqual(MODULE.model_role(row), "video-generation")

    def test_standard_modality_directions_keep_expected_roles(self):
        cases = {
            "text-generation": "llm",
            "image-to-text": "vlm",
            "audio-text-to-text": "audio-stt",
            "text-to-image": "image-generation",
            "text-to-speech": "audio-tts",
        }
        for pipeline, expected in cases.items():
            with self.subTest(pipeline=pipeline):
                self.assertEqual(
                    MODULE.model_role(model_row("community/model", pipeline_tag=pipeline)),
                    expected,
                )

    def test_unstructured_label_remains_unknown(self):
        row = model_row("community/model", pipeline_tag="experimental-omni-model")
        self.assertEqual(MODULE.model_role(row), "unknown")
        self.assertEqual(MODULE.modality_evidence(row)["signals"], [])

    def test_arxiv_tags_produce_primary_and_hf_paper_links(self):
        row = model_row("community/model", tags=["arxiv:2606.19348"])
        self.assertEqual(
            MODULE.paper_links(row),
            [
                {
                    "id": "2606.19348",
                    "arxiv_url": "https://arxiv.org/abs/2606.19348",
                    "hf_paper_url": "https://huggingface.co/papers/2606.19348",
                }
            ],
        )

    def test_architecture_section_is_extracted_from_card(self):
        card = """# Model\n\nIntro text that is long enough to be selected as a normal paragraph for context.\n\n## Model Architecture\n\nThe model combines an encoder and a transformer backbone for unified generation.\n\n## Usage\n\nInstall the package and run it.\n"""
        excerpt = MODULE.extract_architecture_excerpt(card)
        self.assertIn("encoder and a transformer backbone", excerpt)
        self.assertNotIn("Install the package", excerpt)


class EvaluationEvidenceTests(unittest.TestCase):
    def test_benchmark_table_without_evaluation_heading_is_extracted(self):
        card = """# Model\n\n## Introduction\n\nThe release improves agentic performance on the benchmarks below.\n\n| Benchmark | New | Preview |\n| --- | ---: | ---: |\n| Terminal Bench | 82.7 | 61.8 |\n| Tool Use | 70.3 | 49.7 |\n\nNotes:\n1. The harness is not yet released.\n\n## Usage\n\nRun the model.\n"""
        evidence = MODULE.extract_evaluation_evidence(card)
        self.assertEqual(evidence["source"], "model-card")
        self.assertIn("Terminal Bench | 82.7 | 61.8", evidence["excerpt"])
        self.assertIn("harness is not yet released", evidence["excerpt"])
        self.assertNotIn("Run the model", evidence["excerpt"])

    def test_evaluation_section_keeps_conditions_and_limitations(self):
        card = """# Model\n\n## Evaluation — full results\n\nAll at Q4_K_M in thinking mode on one GPU.\n\n| Test | Result |\n| --- | ---: |\n| HumanEval | 94.5 |\n| SWE-bench subset | 7/15 |\n\n## Limitations\n\nThe subset is small and only Q4_K_M was evaluated.\n"""
        evidence = MODULE.extract_evaluation_evidence(card)
        self.assertIn("Q4_K_M in thinking mode", evidence["excerpt"])
        self.assertIn("HumanEval | 94.5", evidence["excerpt"])
        self.assertIn("subset is small", evidence["caveats"])

    def test_card_without_evaluation_does_not_invent_evidence(self):
        card = """# Model\n\n## Usage\n\nThis paragraph only explains how to run inference locally.\n"""
        self.assertEqual(MODULE.extract_evaluation_evidence(card), {})


class DevelopmentArtifactTests(unittest.TestCase):
    def test_registry_validation_rejects_dangling_artifact_dependency(self):
        projects = {
            "projects": [
                {
                    "id": "broken",
                    "openness": "reproducible",
                    "artifacts": [
                        {
                            "id": "https://github.com/Official/training",
                            "role": "training-recipe",
                            "depends_on": ["missing/artifact"],
                        }
                    ],
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "unknown artifact dependency"):
            MODULE.validate_registries({}, projects, {})

    def test_repository_urls_are_normalized_without_name_inference(self):
        self.assertEqual(
            MODULE.huggingface_repo_from_url(
                "https://huggingface.co/datasets/Official/training-data"
            ),
            ("dataset", "Official/training-data"),
        )
        self.assertEqual(
            MODULE.github_repo_api_url("https://github.com/Official/training/tree/main/recipes"),
            "https://api.github.com/repos/Official/training",
        )
        self.assertEqual(
            MODULE.github_artifact_spec(
                "https://github.com/Official/training/tree/main/recipes/eval"
            )["path"],
            "recipes/eval",
        )

    def test_registered_github_recipe_update_enters_reproducible_project(self):
        url = "https://github.com/Official/training/tree/main/recipes"
        registry = {
            "projects": [
                {
                    "id": "official-project",
                    "name": "Official Project",
                    "url": "https://github.com/Official/training",
                    "scope": "full-chain",
                    "openness": "reproducible",
                    "artifacts": [
                        {
                            "id": url,
                            "repo_type": "url",
                            "role": "training-recipe",
                            "depends_on": [],
                        }
                    ],
                }
            ]
        }
        rows = {
            url: {
                "id": url,
                "createdAt": "2026-01-01T00:00:00Z",
                "lastModified": "2026-07-30T00:00:00Z",
                "url": "https://github.com/Official/training",
                "change_evidence": {
                    "source": "GitHub commit history",
                    "ok": True,
                    "commits": [
                        {
                            "id": "abc",
                            "title": "Update training config",
                            "date": "2026-07-30",
                            "url": "https://github.com/Official/training/commit/abc",
                        }
                    ],
                },
            }
        }
        items = MODULE.project_items(
            registry,
            {},
            {},
            rows,
            dt.date(2026, 7, 27),
            dt.date(2026, 8, 2),
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["metadata"]["artifacts"][0]["role"], "training-recipe")
        self.assertEqual(
            items[0]["metadata"]["artifacts"][0]["change_evidence"]["commits"][0]["title"],
            "Update training config",
        )

    def test_github_subdirectory_requires_path_specific_commit(self):
        root = "https://github.com/Official/training"
        subdirectory = root + "/tree/main/src/eval"
        registry = {
            "projects": [
                {
                    "artifacts": [
                        {"id": root, "repo_type": "url"},
                        {"id": subdirectory, "repo_type": "url"},
                    ]
                }
            ]
        }
        requested_urls = []

        def response(url, **kwargs):
            requested_urls.append(url)
            if "path=src%2Feval" in url:
                return "[]"
            return """[{"sha":"abc","html_url":"https://github.com/Official/training/commit/abc","commit":{"message":"Update dependency","committer":{"date":"2026-07-30T00:00:00Z"}}}]"""

        with mock.patch.object(MODULE, "fetch_text", side_effect=response):
            rows, errors = MODULE.query_project_urls(
                registry,
                dt.date(2026, 7, 27),
                dt.date(2026, 8, 2),
            )
        self.assertEqual(errors, {})
        self.assertIn(root, rows)
        self.assertNotIn(subdirectory, rows)
        self.assertTrue(any("path=src%2Feval" in url for url in requested_urls))

    def test_hf_change_evidence_is_limited_to_window(self):
        payload = [
            {
                "id": "new",
                "title": "Update README.md",
                "date": "2026-08-02T00:00:00Z",
            },
            {
                "id": "old",
                "title": "Old change",
                "date": "2026-07-01T00:00:00Z",
            },
        ]
        with mock.patch.object(MODULE, "hf_api", return_value=payload):
            evidence = MODULE.fetch_hf_change_evidence(
                "Official/model",
                "model",
                dt.date(2026, 7, 27),
                dt.date(2026, 8, 2),
            )
        self.assertTrue(evidence["ok"])
        self.assertEqual([entry["id"] for entry in evidence["commits"]], ["new"])

    def test_official_owner_dataset_can_be_discovered_without_heat_threshold(self):
        row = model_row(
            "Official/training-data",
            createdAt="2026-07-30T00:00:00Z",
            lastModified="2026-07-30T00:00:00Z",
            trendingScore=0,
            downloads=0,
            likes=0,
        )
        items = MODULE.new_dataset_items(
            [row],
            set(),
            {"Official"},
            dt.date(2026, 7, 27),
            dt.date(2026, 8, 2),
        )
        self.assertEqual(len(items), 1)
        self.assertIn("trusted-publisher", items[0]["metadata"]["selection"])
        self.assertNotIn("hot", items[0]["metadata"]["selection"])

    def test_historical_run_ignores_unknown_owner_hot_dataset(self):
        row = model_row(
            "Community/hot-today",
            createdAt="2026-07-30T00:00:00Z",
            lastModified="2026-07-30T00:00:00Z",
            trendingScore=100,
            downloads=100_000,
            likes=1_000,
        )
        items = MODULE.new_dataset_items(
            [row],
            set(),
            {"Official"},
            dt.date(2026, 7, 27),
            dt.date(2026, 8, 2),
            allow_hot_discovery=False,
        )
        self.assertEqual(items, [])

    def test_notable_datasets_balance_trusted_and_hot_signals(self):
        def item(owner, index, selection, score):
            return {
                "title": f"{owner}/dataset-{index}",
                "event": "repository-updated",
                "date": "2026-08-02",
                "metadata": {
                    "selection": selection,
                    "trendingScore": score,
                    "downloads": 1_000,
                    "likes": 20,
                },
            }

        trusted = [
            item(f"Official{index}", index, ["trusted-publisher"], 0)
            for index in range(5)
        ]
        hot = [
            item(f"Community{index}", index, ["hot"], 100 - index)
            for index in range(3)
        ]
        selected = MODULE.select_diverse_datasets(trusted + hot, MODULE.NOTABLE_DATASET_MAX)
        selections = [(entry.get("metadata") or {}).get("selection") or [] for entry in selected]
        self.assertGreaterEqual(sum("trusted-publisher" in value for value in selections), 3)
        self.assertGreaterEqual(sum("hot" in value for value in selections), 2)


class TrendSnapshotTests(unittest.TestCase):
    def test_snapshot_adds_rank_and_metric_deltas(self):
        previous = {
            "version": MODULE.SNAPSHOT_VERSION,
            "observed_at": "2026-08-01",
            "models": {
                "community/model": {
                    "rank": 7,
                    "trendingScore": 10,
                    "downloads": 4_000,
                    "likes": 25,
                }
            },
        }
        rows = [model_row("community/model", trendingScore=20, downloads=5_000, likes=30)]
        MODULE.annotate_trending_deltas(rows, previous)
        self.assertEqual(rows[0]["_trend"]["rank"], 1)
        self.assertEqual(rows[0]["_trend"]["rank_delta"], 6)
        self.assertEqual(rows[0]["_trend"]["score_delta"], 10.0)
        self.assertEqual(rows[0]["_trend"]["downloads_delta"], 1_000)
        self.assertEqual(rows[0]["_trend"]["likes_delta"], 5)

    def test_snapshot_round_trip(self):
        rows = [model_row("community/model")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state" / "trending-snapshot.json"
            MODULE.write_trending_snapshot(path, rows, "2026-08-02")
            snapshot = MODULE.load_trending_snapshot(path)
        self.assertEqual(snapshot["observed_at"], "2026-08-02")
        self.assertEqual(snapshot["models"]["community/model"]["rank"], 1)

    def test_snapshot_write_failure_is_non_fatal(self):
        rows = [model_row("community/model")]
        with tempfile.TemporaryDirectory() as directory:
            blocker = Path(directory) / "not-a-directory"
            blocker.write_text("blocked", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                written = MODULE.write_trending_snapshot_safely(
                    blocker / "trending-snapshot.json",
                    rows,
                    "2026-08-02",
                )
        self.assertFalse(written)
        self.assertIn("HF_TREND_SNAPSHOT_SKIPPED", stderr.getvalue())

    def test_historical_output_strips_live_popularity(self):
        item = {
            "metadata": {
                "trendingScore": 20,
                "downloads": 5_000,
                "likes": 30,
                "trend": {"rank": 1},
                "selection": ["priority"],
            }
        }
        MODULE.strip_live_popularity([item])
        self.assertEqual(item["metadata"], {"selection": ["priority"]})


class HistoricalMainTests(unittest.TestCase):
    def test_historical_main_skips_live_pools_and_removes_popularity(self):
        local_id = "Qwen/Qwen3.6-35B-A3B-FP8"
        row = model_row(
            local_id,
            createdAt="2026-01-01T00:00:00Z",
            lastModified="2026-07-30T00:00:00Z",
            trendingScore=100,
            downloads=1_000_000,
            likes=1_000,
        )
        captured = {}

        def capture_payload(payload, output):
            captured.update(payload)

        dataset_query = mock.Mock(return_value=([], {"trending": 0, "recent": 0, "official_owner": 0, "union": 0}, {}))
        with (
            mock.patch.object(MODULE, "query_owner_models", return_value=([row], {}, {})),
            mock.patch.object(MODULE, "query_local_candidates", side_effect=AssertionError("live local query")),
            mock.patch.object(MODULE, "query_global_models", side_effect=AssertionError("live global query")),
            mock.patch.object(MODULE, "query_dataset_candidates", dataset_query),
            mock.patch.object(MODULE, "query_project_urls", return_value=({}, {})),
            mock.patch.object(MODULE, "fetch_many", return_value=({}, {})),
            mock.patch.object(MODULE, "enrich_items_with_cards", side_effect=lambda items, *args: items),
            mock.patch.object(MODULE, "emit_payload", side_effect=capture_payload),
            mock.patch("sys.argv", ["open_source_updates.py", "--date", "2026-07-27"]),
        ):
            self.assertEqual(MODULE.main(), 0)

        dataset_query.assert_called_once()
        self.assertFalse(dataset_query.call_args.args[1])
        local_items = captured["groups"]["local"]
        self.assertEqual([item["title"] for item in local_items], [local_id])
        metadata = local_items[0]["metadata"]
        self.assertEqual(metadata["selection"], ["priority"])
        self.assertNotIn("trendingScore", metadata)
        self.assertNotIn("downloads", metadata)
        self.assertNotIn("likes", metadata)
        self.assertNotIn("trend", metadata)
        self.assertEqual(captured["diagnostics"]["local_hot_before_limit"], 0)


class LocalVariantTests(unittest.TestCase):
    def test_explicit_variants_share_one_representative(self):
        def item(model_id, score):
            return {
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "date": "2026-08-02",
                "metadata": {
                    "base_models": ["Official/base"],
                    "derivation": ["quantized"],
                    "deployment": ["gguf"],
                    "variant_group": "base-quants",
                    "selection": ["hot"],
                    "trendingScore": score,
                    "downloads": score * 100,
                    "likes": score,
                },
            }

        collapsed = MODULE.collapse_local_variants(
            [item("Community/base-GGUF-A", 20), item("Community/base-GGUF-B", 10)]
        )
        self.assertEqual(len(collapsed), 1)
        self.assertEqual(collapsed[0]["title"], "Community/base-GGUF-A")
        self.assertEqual(len(collapsed[0]["metadata"]["variants"]), 2)

    def test_same_publisher_and_base_are_not_implicitly_collapsed(self):
        def item(model_id):
            return {
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "date": "2026-08-02",
                "metadata": {
                    "base_models": ["Official/base"],
                    "derivation": ["quantized"],
                    "deployment": ["gguf"],
                    "selection": ["hot"],
                    "trendingScore": 20,
                    "downloads": 2_000,
                    "likes": 20,
                },
            }

        collapsed = MODULE.collapse_local_variants(
            [item("Community/agentic-GGUF"), item("Community/coder-GGUF")]
        )
        self.assertEqual(len(collapsed), 2)

    def test_different_publishers_are_not_collapsed(self):
        def item(model_id):
            return {
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "date": "2026-08-02",
                "metadata": {
                    "base_models": ["Official/base"],
                    "derivation": ["quantized"],
                    "deployment": ["gguf"],
                    "selection": ["hot"],
                    "trendingScore": 20,
                    "downloads": 2_000,
                    "likes": 20,
                },
            }

        collapsed = MODULE.collapse_local_variants(
            [item("PublisherA/base-GGUF"), item("PublisherB/base-Fusion-GGUF")]
        )
        self.assertEqual(len(collapsed), 2)

    def test_selection_reserves_bounded_publisher_diversity(self):
        def item(model_id, score, publisher_tier):
            return {
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}",
                "date": "2026-08-02",
                "metadata": {
                    "publisher_tier": publisher_tier,
                    "base_models": [],
                    "derivation": ["finetune"],
                    "deployment": [],
                    "selection": ["hot"],
                    "trendingScore": score,
                    "downloads": 5_000,
                    "likes": 30,
                },
            }

        diverse = [
            item(f"Publisher{index}/model", 30 - index, "unregistered")
            for index in range(MODULE.LOCAL_PUBLISHER_COVERAGE_MAX)
        ]
        generic = [
            item(f"Dominant/model-{index}", 100 - index, "unregistered")
            for index in range(MODULE.LOCAL_REPORT_MAX)
        ]
        selected = MODULE.select_popular_derivatives(diverse + generic)
        selected_titles = {entry["title"] for entry in selected}
        self.assertEqual(len(selected), MODULE.LOCAL_REPORT_MAX)
        self.assertTrue({entry["title"] for entry in diverse} <= selected_titles)


if __name__ == "__main__":
    unittest.main()
