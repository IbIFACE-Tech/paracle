"""Review exception types."""


class ReviewError(Exception):
    """Base exception for review-related errors."""

    def __init__(self, message: str, review_id: str | None = None):
        """Initialize review error.

        Args:
            message: Error message
            review_id: Optional review identifier
        """
        super().__init__(message)
        self.review_id = review_id


class ReviewNotFoundError(ReviewError):
    """Raised when review is not found."""

    pass


class ReviewAlreadyDecidedError(ReviewError):
    """Raised when attempting to modify decided review."""

    pass


class InsufficientApprovalsError(ReviewError):
    """Raised when approvals are insufficient."""

    def __init__(
        self,
        message: str,
        review_id: str | None = None,
        current_approvals: int = 0,
        required_approvals: int = 1,
    ):
        """Initialize insufficient approvals error.

        Args:
            message: Error message
            review_id: Review identifier
            current_approvals: Current approval count
            required_approvals: Required approval count
        """
        super().__init__(message, review_id)
        self.current_approvals = current_approvals
        self.required_approvals = required_approvals


class ReviewTimeoutError(ReviewError):
    """Raised when review times out."""

    pass
