import pytz
import logging
from typing import Tuple
from datetime import datetime

from .query_functions import ftr


__all__ = [
    "DateRange",
    "to_dynamics_date_format",
    "from_dynamics_date_format",
]


logger = logging.getLogger(__name__)


def to_dynamics_date_format(date: datetime, from_timezone: str = None) -> str:
    """Convert a datetime-object to a Dynamics compatible ISO formatted date string.

    :param date: Datetime object.
    :param from_timezone: Name of the timezone, from 'pytz.all_timezones', the date is in.
                          Dynamics dates are in UCT, so timezoned values need to be converted to it.
    """

    if from_timezone is not None and date.tzinfo is None:
        tz = pytz.timezone(from_timezone)
        date: datetime = tz.localize(date)

    if date.tzinfo is not None:
        date -= date.utcoffset()

    return date.replace(tzinfo=None).isoformat(timespec="seconds") + "Z"


def from_dynamics_date_format(date: str, to_timezone: str = "UCT") -> datetime:
    """Convert a Dynamics compatible ISO formatted date string to a datetime-object.

    :param date: Date string in form: YYYY-mm-ddTHH:MM:SSZ
    :param to_timezone: Name of the timezone, from 'pytz.all_timezones', to convert the date to.
                        This won't add 'tzinfo', instead the actual time part will be changed from UTC
                        to what the time is at 'to_timezone'.
    """
    tz = pytz.timezone(to_timezone)
    local_time: datetime = tz.localize(datetime.fromisoformat(date.replace("Z", "")))
    local_time += local_time.utcoffset()
    local_time = local_time.replace(tzinfo=None)
    return local_time


class DateRange:
    """Object for creating now, start, and end dates in datetime and dynamics
    compatible ISO string format. Also compiles an appropriate dynamics filter,
    but note that this only takes into account the date, and not the time part.
    """

    def __init__(self, start: datetime = None, end: datetime = None, start_key: str = None, end_key: str = None):

        if start and not start_key:
            raise ValueError("Dynamics table date start key needed if start defined.")
        if end and not end_key:
            raise ValueError("Dynamics table date end key needed if end defined.")

        self.filter_range = []
        self.start_date = start
        self.end_date = end
        self.start_string = ""
        self.end_string = ""

        if start is not None:
            self.start_string = to_dynamics_date_format(start)
            self.filter_range.append(ftr.on_or_after(end_key, self.start_string))

        if end is not None:
            self.end_string = to_dynamics_date_format(end)
            self.filter_range.append(ftr.on_or_before(start_key, self.end_string))

    def __contains__(self, item: Tuple[str, str]) -> bool:
        """Check if (start, end) dynamics ISO formatted strings are in the defined range."""
        try:
            booking_start = from_dynamics_date_format(item[0])
            booking_end = from_dynamics_date_format(item[1])
        except Exception:  # noqa
            logger.error(f"Bad date values, either '{item[0]}' or '{item[1]}'.")
            return False

        if self.start_date and booking_end < self.start_date:
            return False
        if self.end_date and booking_start >= self.end_date:
            return False

        return True
