#!/usr/bin/env python
import re

async def parse_args(func, params, param_str):
    while param_str:
        match = re.match(r'((\S+)=(\S+) *)', param_str)
        params[match.group(2)] = match.group(3)
        param_str = param_str.replace(match.group(1), "")

    await func(params)
