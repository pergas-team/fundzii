from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    # Normalize to {'errors': {...}} to preserve existing API contract.
    data = response.data
    if isinstance(data, dict) and 'errors' not in data:
        if 'detail' in data and len(data) == 1:
            response.data = {'errors': {'detail': str(data['detail'])}}
        else:
            response.data = {'errors': data}
    elif not isinstance(data, dict):
        response.data = {'errors': {'detail': str(data)}}

    # DRF maps unauthenticated → 403 with SessionAuthentication; enforce 401.
    if isinstance(exc, NotAuthenticated):
        response.status_code = status.HTTP_401_UNAUTHORIZED

    return response
