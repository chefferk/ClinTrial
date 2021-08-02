"""Basic utilities module"""
import requests
import csv
import re


def request_ct(url):
    """Performs a get request that provides a (somewhat) useful error message."""
    try:
        response = requests.get(url)
    except ImportError:
        raise ImportError(
            "Couldn't retrieve the data, check your search expression or try again later."
        )
    else:
        return response


def json_handler(url):
    """Returns request in JSON (dict) format"""
    return request_ct(url).json()
