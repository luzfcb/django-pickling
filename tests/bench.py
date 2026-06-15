import pytest
import pickle
from django.db.models import Model
import django_pickling

pytestmark = pytest.mark.django_db

from .test_db import post


def bench_dumps_regular(benchmark, post):
    # Restore original reduce for regular Django model pickling
    orig_reduce = Model.__reduce__
    Model.__reduce__ = django_pickling.original_Model__reduce__
    try:
        benchmark(pickle.dumps, post, -1)
    finally:
        Model.__reduce__ = orig_reduce


def bench_dumps_django_pickling(benchmark, post):
    # Ensure django-pickling reduce is used
    orig_reduce = Model.__reduce__
    Model.__reduce__ = django_pickling.Model__reduce__
    try:
        benchmark(pickle.dumps, post, -1)
    finally:
        Model.__reduce__ = orig_reduce


def bench_loads_regular(benchmark, post):
    # Dump using regular pickling
    orig_reduce = Model.__reduce__
    Model.__reduce__ = django_pickling.original_Model__reduce__
    try:
        stored = pickle.dumps(post, -1)
    finally:
        Model.__reduce__ = orig_reduce

    # Load using regular Django behavior
    benchmark(pickle.loads, stored)


def bench_loads_django_pickling(benchmark, post):
    # Dump using django-pickling
    orig_reduce = Model.__reduce__
    Model.__reduce__ = django_pickling.Model__reduce__
    try:
        stored = pickle.dumps(post, -1)
    finally:
        Model.__reduce__ = orig_reduce

    # Load using django-pickling
    benchmark(pickle.loads, stored)

