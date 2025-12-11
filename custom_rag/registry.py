import json
import importlib
from pathlib import Path
from typing import Any, Dict, Tuple, Type


class PipelineRegistry:
    """Registry for loading and managing pipeline configurations."""

    def __init__(self):
        """Initialize registry and load pipeline configurations."""
        self.config_path = Path(__file__).parent / "pipelines.json"
        self.pipelines = {}
        self.load_config()

    def load_config(self) -> None:
        """Load pipeline configurations from pipelines.json."""
        with open(self.config_path, "r") as f:
            self.pipelines = json.load(f)

    def reload_config(self) -> None:
        """Reload pipeline configurations without server restart."""
        self.load_config()

    def get_pipeline(
        self,
        function_id: str,
        request_data: Dict[str, Any]
    ) -> Tuple[Type, Dict[str, Any], Dict[str, Any]]:
        """
        Get pipeline class, config, and context for a function_id.

        Args:
            function_id: Pipeline function identifier
            request_data: Request data from API call

        Returns:
            Tuple of (pipeline_class, config, context)

        Raises:
            ValueError: If function_id not found or pipeline cannot be loaded
        """
        if function_id not in self.pipelines:
            raise ValueError(f"Pipeline '{function_id}' not found in registry")

        pipeline_config = self.pipelines[function_id]
        pipeline_path = pipeline_config["pipeline"]
        config = pipeline_config["config"]

        pipeline_class = self._import_pipeline_class(pipeline_path)

        context = self._build_context(request_data)

        return pipeline_class, config, context

    def _import_pipeline_class(self, pipeline_path: str) -> Type:
        """
        Dynamically import pipeline class from module path.

        Args:
            pipeline_path: Full module path to pipeline class
                          (e.g., 'custom_rag.pipelines.company_a.pipeline.RAGPipeline')

        Returns:
            Pipeline class

        Raises:
            ValueError: If pipeline class cannot be imported
        """
        try:
            module_path, class_name = pipeline_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            pipeline_class = getattr(module, class_name)
            return pipeline_class
        except (ValueError, ImportError, AttributeError) as e:
            raise ValueError(f"Failed to import pipeline '{pipeline_path}': {e}")

    def _build_context(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context dictionary from request data.

        Args:
            request_data: Request data from API call

        Returns:
            Context dictionary

        Raises:
            ValueError: If 'llm' model is not provided
        """
        llm = request_data.get("llm")
        if not llm:
            raise ValueError("'llm' model must be provided in request")

        return {
            "prompt_objects": request_data.get("prompt_objects", {}),
            "scope_variables": request_data.get("scope_variables", {}),
            "previous_prompt_outputs": request_data.get("previous_prompt_outputs", {}),
            "llm": llm,
        }


registry = PipelineRegistry()
