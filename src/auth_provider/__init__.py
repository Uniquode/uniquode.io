"""Deferred internal Authlib integration boundary for OAuth2 provider work.

This package is intentionally independent of FastAPI Users and `auth_ext`.
Implementation waits until local users and authorisation scopes/groups are
stable enough to provide subject, client, grant, token, consent, and scope
interfaces.
"""
