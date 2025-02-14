import logging

from django.urls import resolve

logger = logging.getLogger(__name__)


class DebugMiddleware:
    """
    Middleware for debugging purposes.
    To use this middleware, add "ACTIVATE_DJANGO_DEBUG_MIDDLEWARE=True" to your .env file.
    Before making the action you want to investigate in the frontend:
    - Add a breakpoint to 'response = self.get_response(request)'.
    - Any request made to the server will hit that line.
    - Investigate the request object from the frontend after it was handled by other middlewares.
    - Step into self.get_response to investigate which part of the code handled that request.
    - Investigate the response variable representing the response returned by the server for that request.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Log request info
        logger.info(f"Request: {request.method} {request.path}")

        # Resolve view
        myfunc, myargs, mykwargs = resolve(request.path)
        mymodule = myfunc.__module__.replace(".", "/")
        myname = myfunc.__name__
        
        # Check if it's a class-based view
        if hasattr(myfunc, "view_class"):
            view_class_name = myfunc.view_class.__name__
            logger.info(f"View: {mymodule} {myname} (Class: {view_class_name}) {myargs} {mykwargs}")
        else:
            logger.info(f"View: {mymodule} {myname} {myargs} {mykwargs}")

        response = self.get_response(request)
        
        # Log response info
        template_name = getattr(response, "template_name", None)
        if template_name:
            logger.info(f"Response: {template_name}")
        
        return response
