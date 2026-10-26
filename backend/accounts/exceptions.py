from collections.abc import Mapping

from rest_framework import status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _validation_error_type(error):
    code = str(getattr(error, "code", "invalid"))
    return {
        "required": "missing",
        "blank": "string_too_short",
        "min_length": "string_too_short",
        "max_length": "string_too_long",
        "null": "string_type",
        "extra_forbidden": "extra_forbidden",
    }.get(code, code)


def _collect_validation_errors(detail, location=()):
    if isinstance(detail, Mapping):
        for field, nested in detail.items():
            next_location = location if field == "non_field_errors" else (*location, str(field))
            yield from _collect_validation_errors(nested, next_location)
        return
    if isinstance(detail, (list, tuple)):
        for nested in detail:
            yield from _collect_validation_errors(nested, location)
        return

    error_type = _validation_error_type(detail)
    message = str(detail)
    if error_type == "missing":
        message = "Field required"
    elif error_type == "extra_forbidden":
        message = "Extra inputs are not permitted"
    yield {
        "loc": ["body", *location] if location else ["body"],
        "msg": message,
        "type": error_type,
    }


def openapi_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response(
            {"detail": list(_collect_validation_errors(exc.detail))},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if isinstance(exc, ParseError):
        return Response(
            {"detail": [{"loc": ["body"], "msg": str(exc.detail), "type": "json_invalid"}]},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return exception_handler(exc, context)
