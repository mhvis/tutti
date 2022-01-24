import os


def source_commit(request):
    """Retrieves commit hash from environment."""
    return {
        # "SOURCE_COMMIT": "sdf"
        "SOURCE_COMMIT": os.getenv("SOURCE_COMMIT")
    }
