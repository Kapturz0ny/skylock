"""Extra functions that did not fit anywhere"""

def stringify_size(size: int, decimals: int = 1) -> str:
    """Converts a given size in bytes to a human-readable string representation.

    The size is converted to the most appropriate unit (B, kB, MB, GB, TB).

    Args:
        size (int): The size in bytes.
        decimals (int, optional): The number of decimal places to include for
            non-byte units. Defaults to 1.

    Returns:
        str: A string representing the size with its unit, e.g., "10.5 MB".
    """
    suffix_list = ["B", "kB", "MB", "GB", "TB"]
    current = float(size)
    i = 0

    while current >= 1024 and i < len(suffix_list) - 1:
        i += 1
        current /= 1024

    if i == 0:
        return f"{int(current)} {suffix_list[i]}"
    return f"{current:.{decimals}f} {suffix_list[i]}"
