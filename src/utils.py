from croniter import croniter

def validate_cron_expr(expr):
    """Validate a cron expression. Accepts string or list, raises ValueError if invalid."""
    if isinstance(expr, list):
        expr = " ".join(expr)
    try:
        croniter(str(expr))
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {expr}. Error: {e}")
    return True