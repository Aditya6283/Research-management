class ForceHTTPSScheme:
    """
    UQCloud terminates SSL at the load balancer and sends plain HTTP to Nginx.
    Nginx's researchdoc location block passes X-Forwarded-Proto: http (using
    $scheme, not $_scheme), so Django cannot detect HTTPS automatically.
    This middleware forces wsgi.url_scheme to 'https' so that
    request.build_absolute_uri() produces https:// URLs, which is required
    for Google OAuth callback URLs to match what's registered in Google Console.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['wsgi.url_scheme'] = 'https'
        return self.get_response(request)
