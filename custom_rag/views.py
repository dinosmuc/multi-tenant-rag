import json

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from custom_rag.registry import registry
from custom_rag.utils import ErrorCodes, error_response, success_response


@csrf_exempt
@require_http_methods(["POST"])
def execute_pipeline(request):
    """
    Execute a RAG pipeline based on function_id.

    Request Format:
        {
            "function_id": "<function_id>",
            "llm_provider": "<provider_name>",
            "llm": "<model_name>",
            "reasoning_effort": "<effort_level>",  // optional
            "prompt_objects": {...},
            "scope_variables": {...},
            "previous_prompt_outputs": {...}
        }

    Success Response:
        {
            "success": true,
            "statusCode": 200,
            "data": {
                "output": {...},
                "metadata": {
                    "iterations": <number>,
                    "tools_used": [...]
                }
            },
            "usage": {
                "input_tokens": <number>,
                "output_tokens": <number>,
                "total_tokens": <number>
            }
        }

    Error Response:
        {
            "success": false,
            "statusCode": <code>,
            "error": {
                "code": "<ERROR_CODE>",
                "message": "<error_message>"
            },
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        }
    """
    try:
        request_data = json.loads(request.body)

        function_id = request_data.get("function_id")
        if not function_id:
            return error_response(
                code=ErrorCodes.INVALID_REQUEST,
                message="Missing 'function_id' in request",
                status=400,
            )

        pipeline_class, config, context = registry.get_pipeline(
            function_id, request_data
        )

        with pipeline_class(config) as pipeline:
            result = pipeline.execute(context)

        usage = result.get("usage", {})

        return success_response(
            data={
                "output": result.get("output"),
                "metadata": {
                    "iterations": result.get("iterations", 0),
                    "tools_used": result.get("tools_used", []),
                },
            },
            usage=usage,
        )

    except json.JSONDecodeError:
        return error_response(
            code=ErrorCodes.INVALID_JSON,
            message="Invalid JSON in request body",
            status=400,
        )

    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            code = ErrorCodes.PIPELINE_NOT_FOUND
            status = 404
        elif "provider" in error_message.lower():
            code = ErrorCodes.PROVIDER_NOT_SUPPORTED
            status = 400
        else:
            code = ErrorCodes.INVALID_REQUEST
            status = 400

        return error_response(
            code=code,
            message=error_message,
            status=status,
        )

    except Exception as e:
        return error_response(
            code=ErrorCodes.INTERNAL_ERROR,
            message=f"Internal error: {str(e)}",
            status=500,
        )
