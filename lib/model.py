# (c) E-kvadrat Consulting & Media, 2021

from typing import NamedTuple

class RequestResult(NamedTuple):
    year: int
    start: int
    count: int
    ok: bool
    response: str

