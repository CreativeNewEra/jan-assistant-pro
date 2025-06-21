import asyncio
import os
import sys
from unittest.mock import patch, AsyncMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.retry import retry
from src.core.exceptions import RetryableError


class CustomError(RetryableError):
    pass


@retry(max_attempts=3, initial_delay=0, backoff_factor=1, exceptions=(CustomError,))
async def flaky_async(counter):
    counter['count'] += 1
    if counter['count'] < 3:
        raise CustomError('fail')
    return 'ok'


@retry(max_attempts=2, initial_delay=0, backoff_factor=1, exceptions=(CustomError,))
def always_fail(counter):
    counter['count'] += 1
    raise CustomError('fail')


@retry(max_attempts=3, initial_delay=0.1, backoff_factor=2, exceptions=(CustomError,))
def fail_then_succeed(counter):
    counter['count'] += 1
    if counter['count'] < 3:
        raise CustomError('fail')
    return 'done'


@pytest.mark.asyncio
async def test_retry_success_after_retries_async():
    counter = {'count': 0}
    result = await flaky_async(counter)
    assert result == 'ok'
    assert counter['count'] == 3


def test_retry_exhausts_after_max_attempts():
    counter = {'count': 0}
    with pytest.raises(CustomError):
        always_fail(counter)
    assert counter['count'] == 2


def test_retry_backoff_timing():
    counter = {'count': 0}
    sleep_durations = []

    def fake_sleep(dur):
        sleep_durations.append(dur)

    with patch('src.core.retry.time.sleep', side_effect=fake_sleep):
        result = fail_then_succeed(counter)
    assert result == 'done'
    assert sleep_durations == [0.1, 0.2]
