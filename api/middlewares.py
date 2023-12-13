from django.views.decorators.csrf import csrf_exempt

class CsrfExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith('/api/'):
            request.csrf_processing_done = True  # Disable CSRF processing for this request
            return csrf_exempt(self.get_response)(request)
        return self.get_response(request)