from rest_framework.views import exception_handler


def slims_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict):
            errors = []
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    for message in messages:
                        errors.append(f"{field}: {message}")
                else:
                    errors.append(f"{field}: {messages}")
            response.data = {'data': [], 'message': 'Validation error', 'errors': errors}
        elif isinstance(response.data, list):
            response.data = {'data': [], 'message': 'Validation error', 'errors': response.data}
        else:
            response.data = {'data': [], 'message': 'An unknown error occurred', 'errors': [str(response.data)]}
    return response