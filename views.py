import json
import math
from datetime import datetime, timedelta
from typing import TypedDict

from dateutil.relativedelta import relativedelta
from werkzeug import Response
from werkzeug import Request


class Loan(TypedDict):
    monthly_payment_amount: int
    payment_due_date: int
    schedule_type: str
    debit_start_date: str
    debit_day_of_week: str


class Debit(TypedDict):
    amount: int
    date: str


def get_next_debit_view(request: Request) -> Response:
    """
    View for handling posts for next debit.
    """
    post_body = request.get_json()
    debit = get_next_debit(post_body)
    return Response(json.dumps({"debit": debit}), mimetype='application/json')


def get_next_debit(post_body) -> Debit:
    """Gets the loan post data and passes it to calc function associated
    with that particular pay schedule and returns a debit."""
    loan: Loan = post_body.get('loan')
    schedules = {
        'biweekly': calc_biweekly,
    }
    calc_debit = schedules.get(loan.get('schedule_type'), calc_biweekly)
    return calc_debit(loan)


def calc_biweekly(loan: Loan) -> Debit:
    start_date = datetime.strptime(loan['debit_start_date'], '%Y-%m-%d').date()
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    weekend = {5, 6}
    if tomorrow.weekday() in weekend:
        tomorrow = tomorrow + timedelta((0 - tomorrow.weekday()) % 7)
    if start_date > tomorrow:
        tomorrow = start_date

    schedule = schedule_table(start_date, tomorrow)
    deb_date = next_debit_date(tomorrow, schedule)
    number_of_payments = len(schedule.get(f'{deb_date.year}-{deb_date.month}'))
    amount = math.ceil(loan['monthly_payment_amount'] / number_of_payments)
    return {'amount': amount, 'date': deb_date.strftime('%Y-%m-%d')}


def next_debit_date(current_date: datetime.date, schedule: dict) -> datetime.date:
    """
    Gets the next debit date from the schedule table
    Gets all the pay dates for the current date's month and iterates
    through them until it finds one that is greater than or equal to it.
    """
    debit_date = None
    month_schedule = schedule.get(f'{current_date.year}-{current_date.month}')
    for date in month_schedule:
        if date >= current_date:
            debit_date = date
            break
    if not debit_date:
        next_month = current_date + relativedelta(months=1)
        # if pay date isn't in the current month schedule it should
        # be the first pay date of the next month
        debit_date = schedule.get(f'{next_month.year}-{next_month.month}')[0]
    return debit_date


def schedule_table(start_date: datetime.date, target_date: datetime.date) -> dict:
    """
    Creates a schedule table that groups all the pay dates for a
    given month. I.e. for the month of june, july ect. these are
    all the pay dates in that month.
    Pay dates are based on a biweekly schedule.
    """
    end_date = target_date + relativedelta(months=2)
    months_schedule = {f'{start_date.year}-{start_date.month}': [start_date]}
    while start_date <= end_date:
        start_date += timedelta(days=14)
        months_schedule.setdefault(f'{start_date.year}-{start_date.month}', []).append(start_date)
    return months_schedule
