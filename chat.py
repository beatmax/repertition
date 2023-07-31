import sys


def default_send(msg):
    print(msg, file=sys.stderr)


send_func = default_send


def set_send_func(f):
    global send_func
    send_func = f


def send(msg):
    send_func(msg)
