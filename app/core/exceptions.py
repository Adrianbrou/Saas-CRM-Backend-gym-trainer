"""
exceptions.py - Domain exceptions for the service layer.

Services raise these typed errors instead of a bare ValueError. Two benefits:

  1. The API boundary maps each cause to the correct HTTP status in exactly ONE place
     (the exception handlers registered in app/main.py), so the mapping is consistent
     across every router instead of hand-written per route.

  2. The handler catches each specific type, never the broad ValueError base, so an
     unrelated ValueError raised by an actual bug is no longer silently disguised as a
     friendly 404/400 - it surfaces as a real 500 the way it should.

They subclass ValueError only for backward compatibility with existing call sites and
tests; nothing catches them by the ValueError base.
"""


class AppError(ValueError):
    """Base class for expected domain errors that map to an HTTP status."""


class NotFoundError(AppError):
    """A requested resource does not exist. Maps to HTTP 404."""


class DuplicateError(AppError):
    """A resource already exists or would violate uniqueness. Maps to HTTP 409."""


class BusinessRuleError(AppError):
    """A well-formed request that violates a business rule. Maps to HTTP 400."""
