"""Web runtime package: route modules + shared context (Phase 26).

The FastAPI app is assembled in `holdspeak.web_server.MeetingWebServer`. Phase 26
moves the route handlers out of that monolith's `_create_app` into cohesive
`holdspeak.web.routes` modules, which read shared accessors from
`holdspeak.web.context.WebContext` instead of closing over the server instance.
"""
