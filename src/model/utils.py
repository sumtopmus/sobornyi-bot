from datetime import date, timedelta


def this_week() -> date:
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    return this_monday


def next_week() -> date:
    next_monday = this_week() + timedelta(days=7)
    return next_monday
