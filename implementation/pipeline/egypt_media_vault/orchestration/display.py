"""
Console display helpers shared by every stage (leaf module).
"""




def print_section(title: str) -> None:
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def print_issue(issue) -> None:
    severity = getattr(issue, "severity", "UNKNOWN")
    field_name = getattr(issue, "field_name", "N/A")
    message = getattr(issue, "message", str(issue))

    print(
        f"  [{severity}] "
        f"Field: {field_name} | "
        f"{message}"
    )
