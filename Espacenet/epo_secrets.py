# -*- coding: utf-8 -*-
import os


def get_secret():
    if 'EPO_CLIENT_ID' in os.environ:
        client_id = os.environ['EPO_CLIENT_ID']
    else:
        raise Exception("Set EPO_CLIENT_ID environment variable before continuing")

    if 'EPO_CLIENT_SECRET' in os.environ:
        client_secret = os.environ['EPO_CLIENT_SECRET']
    else:
        raise Exception("Set EPO_CLIENT_SECRET environment variable before continuing")

    if not client_id or not client_secret:
        raise AssertionError()

    return {
            "client_id" : client_id,
            "client_secret" : client_secret
        }
