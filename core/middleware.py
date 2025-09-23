from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import AccessModel


class GlobalAccessMiddleware(MiddlewareMixin):
    """
    Middleware to control global site access based on AccessModel settings.
    /admin/ is always allowed.
    """

    def process_request(self, request):
        try:
            # Get the current URL name (useful if you want finer controls later)
            resolver_match = resolve(request.path_info)
            current_path = request.path_info

            # Allow admin always
            if current_path.startswith("/@gig-admin/"):
                return None

            # Check if global site access is allowed
            access_control = AccessModel.objects.filter(mode="site_access").first()

            if access_control and not access_control.allowed:
                return JsonResponse(
                    {
                        "detail": access_control.description
                        or "Access to this site is currently restricted."
                    },
                    status=403,
                )
        except Exception:
            # Fail safe (e.g., before migrations)
            return None
