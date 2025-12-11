from typing import Any

from django.http import JsonResponse


class ErrorCodes:
    """Standard error codes for the API."""

    INVALID_REQUEST = "INVALID_REQUEST"
    PIPELINE_NOT_FOUND = "PIPELINE_NOT_FOUND"
    PROVIDER_NOT_SUPPORTED = "PROVIDER_NOT_SUPPORTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_JSON = "INVALID_JSON"


def success_response(
    data: dict[str, Any],
    usage: dict[str, int] | None = None,
    status: int = 200,
) -> JsonResponse:
    """
    Create a standardized success response.

    Args:
        data: Response data
        usage: Token usage information
        status: HTTP status code

    Returns:
        JsonResponse with standardized format
    """
    response_data = {
        "success": True,
        "statusCode": status,
        "data": data,
    }

    if usage:
        response_data["usage"] = usage

    return JsonResponse(response_data, status=status)


def error_response(
    code: str,
    message: str,
    status: int = 400,
    usage: dict[str, int] | None = None,
) -> JsonResponse:
    """
    Create a standardized error response.

    Args:
        code: Error code (use ErrorCodes class)
        message: Error message
        status: HTTP status code
        usage: Optional token usage information

    Returns:
        JsonResponse with standardized error format
    """
    response_data = {
        "success": False,
        "statusCode": status,
        "error": {
            "code": code,
            "message": message,
        },
    }

    if usage:
        response_data["usage"] = usage
    else:
        response_data["usage"] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    return JsonResponse(response_data, status=status)
