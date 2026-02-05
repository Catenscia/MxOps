import pytest
import yaml

from mxops.utils.chain_simulator import (
    ALL_SERVICES,
    filter_docker_compose,
    resolve_services,
)


class TestResolveServices:
    def test_default_returns_all_services(self):
        # When
        result = resolve_services()

        # Then
        assert set(result) == set(ALL_SERVICES)

    def test_include_single_service_with_dependencies(self):
        # When
        result = resolve_services(include=["chain-simulator"])

        # Then
        # chain-simulator depends on elasticsearch and events-notifier
        # events-notifier depends on redis
        expected = {"chain-simulator", "elasticsearch", "events-notifier", "redis"}
        assert set(result) == expected

    def test_include_service_without_dependencies(self):
        # When
        result = resolve_services(include=["redis"])

        # Then
        assert set(result) == {"redis"}

    def test_include_multiple_services_with_dependencies(self):
        # When
        result = resolve_services(include=["api", "chain-simulator"])

        # Then
        # api depends on elasticsearch and redis
        # chain-simulator depends on elasticsearch and events-notifier
        # events-notifier depends on redis
        assert set(result) == {
            "api",
            "chain-simulator",
            "elasticsearch",
            "events-notifier",
            "redis",
        }

    def test_exclude_services(self):
        # When
        result = resolve_services(exclude=["explorer", "lite-wallet"])

        # Then
        assert "explorer" not in result
        assert "lite-wallet" not in result
        assert len(result) == len(ALL_SERVICES) - 2

    def test_include_and_exclude_combined(self):
        # When
        result = resolve_services(
            include=["chain-simulator", "api"],
            exclude=["redis"]
        )

        # Then
        # chain-simulator and api both have redis as a transitive dependency
        # but redis is excluded
        assert "redis" not in result
        assert "chain-simulator" in result
        assert "api" in result

    def test_no_auto_deps(self):
        # When
        result = resolve_services(
            include=["chain-simulator"],
            auto_include_dependencies=False
        )

        # Then
        # Without auto deps, only the explicitly requested service is returned
        assert result == ["chain-simulator"]

    def test_no_auto_deps_with_multiple_services(self):
        # When
        result = resolve_services(
            include=["redis", "elasticsearch"],
            auto_include_dependencies=False
        )

        # Then
        assert set(result) == {"redis", "elasticsearch"}

    def test_elastic_indexer_includes_elasticsearch(self):
        # When
        result = resolve_services(include=["elastic-indexer"])

        # Then
        assert set(result) == {"elastic-indexer", "elasticsearch"}

    def test_include_unknown_service_raises_error(self):
        # When / Then
        with pytest.raises(ValueError, match="Unknown services"):
            resolve_services(include=["nonexistent-service"])

    def test_exclude_unknown_service_raises_error(self):
        # When / Then
        with pytest.raises(ValueError, match="Unknown services"):
            resolve_services(exclude=["typo-service"])

    def test_include_mixed_valid_invalid_raises_error(self):
        # When / Then
        with pytest.raises(ValueError, match="Unknown services"):
            resolve_services(include=["redis", "not-a-service"])


class TestFilterDockerCompose:
    @pytest.fixture
    def sample_compose(self):
        return """services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  events-notifier:
    image: multiversx/events-notifier:latest
    depends_on:
      - redis

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.16.1
    ports:
      - "9200:9200"

  chain-simulator:
    image: multiversx/chainsimulator:latest
    depends_on:
      elasticsearch:
        condition: service_healthy
      events-notifier:
        condition: service_healthy
"""

    def test_filter_keeps_selected_services(self, sample_compose):
        # When
        result = filter_docker_compose(sample_compose, ["redis", "elasticsearch"])

        # Then
        parsed = yaml.safe_load(result)
        assert set(parsed["services"].keys()) == {"redis", "elasticsearch"}

    def test_filter_removes_depends_on_for_removed_services(self, sample_compose):
        # When - include only events-notifier without redis
        result = filter_docker_compose(sample_compose, ["events-notifier"])

        # Then
        parsed = yaml.safe_load(result)
        assert "events-notifier" in parsed["services"]
        # depends_on should be removed since redis is not included
        assert "depends_on" not in parsed["services"]["events-notifier"]

    def test_filter_handles_dict_depends_on(self, sample_compose):
        # When - include chain-simulator and elasticsearch but not events-notifier
        result = filter_docker_compose(
            sample_compose,
            ["chain-simulator", "elasticsearch"]
        )

        # Then
        parsed = yaml.safe_load(result)
        assert set(parsed["services"].keys()) == {"chain-simulator", "elasticsearch"}
        # depends_on should only contain elasticsearch
        assert parsed["services"]["chain-simulator"]["depends_on"] == {
            "elasticsearch": {"condition": "service_healthy"}
        }

    def test_filter_all_services_unchanged(self, sample_compose):
        # When
        all_services = ["redis", "events-notifier", "elasticsearch", "chain-simulator"]
        result = filter_docker_compose(sample_compose, all_services)

        # Then
        parsed = yaml.safe_load(result)
        assert set(parsed["services"].keys()) == set(all_services)
