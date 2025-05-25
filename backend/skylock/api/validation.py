from fastapi import HTTPException, Path


def validate_path_not_empty(path: str = Path(...)):
    """Validates that the provided path string is not empty or whitespace.

    Args:
        path (str): The path string to validate.

    Returns:
        str: The validated path string if it is not empty.

    Raises:
        HTTPException: If the path is an empty string or contains only whitespace.
    """
    if not path.strip():
        raise HTTPException(status_code=400, detail="Path cannot be an empty string")
    return path
