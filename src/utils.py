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

def parse_cron_expr_for_apscheduler(expr: str) -> dict:
    """
    Parse a cron expression string into a dict of CronTrigger keyword arguments.
    Supports both 5-field (min hour day month dow) and 6-field (sec min hour day month dow) formats.
    """
    if isinstance(expr, list):
        expr = " ".join(expr)
    fields = str(expr).split()
    if len(fields) == 6:
        return {
            'second': fields[0],
            'minute': fields[1],
            'hour': fields[2],
            'day': fields[3],
            'month': fields[4],
            'day_of_week': fields[5],
        }
    elif len(fields) == 5:
        return {
            'minute': fields[0],
            'hour': fields[1],
            'day': fields[2],
            'month': fields[3],
            'day_of_week': fields[4],
        }
    else:
        raise ValueError(f"Invalid cron expression: {expr} (expected 5 or 6 fields, got {len(fields)})")