def stringify_size(size: int, decimals: int = 1) -> str:
    suffix_list = ["B", "kB", "MB", "GB", "TB"]
    current = float(size)
    i = 0

    while current >= 1024 and i < len(suffix_list) - 1:
        i += 1
        current /= 1024

    if i == 0:
        return f"{int(current)} {suffix_list[i]}"
    return f"{current:.{decimals}f} {suffix_list[i]}"
