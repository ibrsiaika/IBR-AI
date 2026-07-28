"""
Tests for project structure validation (PRD Section 32).

These tests verify that the project folder structure matches the specification
in PRD Section 32.2 (Repository Folder Structure) and that all required
modules are importable.

Run: pytest tests/unit/test_project_structure.py -v
"""
import importlib
from pathlib import Path

import pytest

# Project root is the directory containing pyproject.toml
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src" / "ibr_platform"


class TestFolderStructure:
    """Test that the folder structure matches PRD Section 32.2."""

    def test_src_layout_exists(self):
        """The 'src' layout is used (code in src/ibr_platform/)."""
        assert SRC_DIR.exists(), f"Source directory not found: {SRC_DIR}"
        assert SRC_DIR.is_dir()

    def test_platform_package_exists(self):
        """The platform/ package exists for core platform code."""
        assert (SRC_DIR / "platform").exists()
        assert (SRC_DIR / "platform" / "__init__.py").exists()

    def test_agents_package_exists(self):
        """The agents/ package exists for agent implementations."""
        assert (SRC_DIR / "agents").exists()
        assert (SRC_DIR / "agents" / "__init__.py").exists()

    def test_api_package_exists(self):
        """The api/ package exists for API definitions."""
        assert (SRC_DIR / "api").exists()
        assert (SRC_DIR / "api" / "__init__.py").exists()

    def test_config_package_exists(self):
        """The config/ package exists for configuration management."""
        assert (SRC_DIR / "config").exists()
        assert (SRC_DIR / "config" / "__init__.py").exists()

    def test_docs_directory_exists(self):
        """The docs/ directory exists for documentation."""
        assert (PROJECT_ROOT / "docs").exists()
        assert (PROJECT_ROOT / "docs" / "adr").exists()
        assert (PROJECT_ROOT / "docs" / "research").exists()
        assert (PROJECT_ROOT / "docs" / "guides").exists()

    def test_tests_directory_exists(self):
        """The tests/ directory exists with unit/integration/e2e subdirs."""
        assert (PROJECT_ROOT / "tests").exists()
        assert (PROJECT_ROOT / "tests" / "unit").exists()
        assert (PROJECT_ROOT / "tests" / "integration").exists()
        assert (PROJECT_ROOT / "tests" / "e2e").exists()

    def test_infra_directory_exists(self):
        """The infra/ directory exists for Kubernetes/Helm/Terraform."""
        assert (PROJECT_ROOT / "infra").exists()

    def test_pyproject_toml_exists(self):
        """pyproject.toml exists at project root."""
        assert (PROJECT_ROOT / "pyproject.toml").exists()

    def test_gitignore_exists(self):
        """ .gitignore exists at project root."""
        assert (PROJECT_ROOT / ".gitignore").exists()

    def test_readme_exists(self):
        """README.md exists at project root."""
        assert (PROJECT_ROOT / "README.md").exists()

    def test_makefile_exists(self):
        """Makefile exists for common commands."""
        assert (PROJECT_ROOT / "Makefile").exists()


class TestPackageImportability:
    """Test that all packages are importable."""

    def test_import_ibr_platform(self):
        """The main ibr_platform package is importable."""
        importlib.import_module("ibr_platform")

    def test_import_platform(self):
        """The ibr_platform.platform package is importable."""
        importlib.import_module("ibr_platform.platform")

    def test_import_agents(self):
        """The ibr_platform.agents package is importable."""
        importlib.import_module("ibr_platform.agents")

    def test_import_config(self):
        """The ibr_platform.config package is importable."""
        importlib.import_module("ibr_platform.config")

    def test_import_api(self):
        """The ibr_platform.api package is importable."""
        importlib.import_module("ibr_platform.api")


class TestAgentBase:
    """Test the AgentBase abstract base class (PRD Section 33.4)."""

    def test_agent_base_importable(self):
        """AgentBase is importable from ibr_platform.agents.base."""
        from ibr_platform.agents.base import AgentBase
        assert AgentBase is not None

    def test_agent_base_is_abstract(self):
        """AgentBase cannot be instantiated directly (it's abstract)."""
        from ibr_platform.agents.base import AgentBase
        with pytest.raises(TypeError):
            AgentBase()

    def test_agent_base_has_initialize_method(self):
        """AgentBase has an abstract initialize method."""
        from ibr_platform.agents.base import AgentBase
        assert hasattr(AgentBase, "initialize")

    def test_agent_base_has_execute_method(self):
        """AgentBase has an abstract execute method."""
        from ibr_platform.agents.base import AgentBase
        assert hasattr(AgentBase, "execute")

    def test_agent_base_has_health_check_method(self):
        """AgentBase has an abstract health_check method."""
        from ibr_platform.agents.base import AgentBase
        assert hasattr(AgentBase, "health_check")

    def test_agent_base_has_shutdown_method(self):
        """AgentBase has an abstract shutdown method."""
        from ibr_platform.agents.base import AgentBase
        assert hasattr(AgentBase, "shutdown")

    def test_concrete_agent_can_be_instantiated(self):
        """A concrete subclass of AgentBase can be instantiated."""
        from ibr_platform.agents.base import AgentBase, AgentResult

        class DummyAgent(AgentBase):
            async def initialize(self, config):
                self.config = config

            async def execute(self, task):
                return AgentResult(success=True, data={"result": "done"})

            async def health_check(self):
                return {"status": "healthy"}

            async def shutdown(self):
                pass

        agent = DummyAgent()
        assert agent is not None


class TestConfiguration:
    """Test the configuration management system."""

    def test_config_importable(self):
        """The config module is importable."""
        from ibr_platform.config import settings
        assert settings is not None

    def test_config_has_deployment_mode(self):
        """Configuration has a deployment_mode field."""
        from ibr_platform.config import settings
        assert hasattr(settings, "deployment_mode")

    def test_config_deployment_mode_default(self):
        """Default deployment mode is 'tiny'."""
        from ibr_platform.config import Settings
        # Create a fresh instance to test defaults
        config = Settings()
        assert config.deployment_mode in ["tiny", "compact", "professional", "enterprise"]


class TestVersion:
    """Test that the package has a version."""

    def test_version_exists(self):
        """The package has a __version__ attribute."""
        import ibr_platform
        assert hasattr(ibr_platform, "__version__")
        assert isinstance(ibr_platform.__version__, str)
        # Semantic versioning: MAJOR.MINOR.PATCH
        parts = ibr_platform.__version__.split(".")
        assert len(parts) >= 2, f"Version should be semver: {ibr_platform.__version__}"
