def normalize_output(text: str) -> str:
    # Normalize newline styles.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    # Ignore trailing spaces and tabs on each line.
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    # Ignore extra blank lines at the end of the output.
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def compare_output(actual: str, expected: str) -> bool:
    return normalize_output(actual) == normalize_output(expected)