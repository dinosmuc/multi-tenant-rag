import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from custom_rag.registry import registry


@csrf_exempt
@require_http_methods(["POST"])
def execute_pipeline(request):
    """
    Execute a RAG pipeline based on function_id.

    Request Format:
        {
            "function_id": "<function_id>",
            "prompt_objects": {...},
            "scope_variables": {...},
            "previous_prompt_outputs": {...},
            "llm": "<model_name>"
        }

    Success Response:
        {
            "success": true,
            "output": {...},
            "metadata": {
                "iterations": <number>,
                "tools_used": [...]
            }
        }

    Error Response:
        {
            "success": false,
            "error": "<error_message>"
        }
    """
    try:
        request_data = json.loads(request.body)

        function_id = request_data.get("function_id")
        if not function_id:
            return JsonResponse({
                "success": False,
                "error": "Missing 'function_id' in request"
            }, status=400)

        pipeline_class, config, context = registry.get_pipeline(
            function_id,
            request_data
        )

        with pipeline_class(config) as pipeline:
            result = pipeline.execute(context)

        return JsonResponse({
            "success": True,
            "output": result.get("output"),
            "metadata": {
                "iterations": result.get("iterations", 0),
                "tools_used": result.get("tools_used", []),
            }
        })

    except ValueError as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON in request body"
        }, status=400)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Internal error: {str(e)}"
        }, status=500)
