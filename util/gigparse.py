#!/usr/bin/env python
import re

class GigParseException(Exception):
    pass

async def parse_args(func, params, param_str):
    while param_str:
        # first look for arg surrounded by quotes
        match = re.match(r'((\S+)="([^"]+)" *)', param_str)
        if not match:
            match = re.match(r'((\S+)=(\S+) *)', param_str)
        if not match:
            raise GigParseException("Bad param_str")
        params[match.group(2)] = match.group(3)
        param_str = param_str.replace(match.group(1), "")

    await func(params)
