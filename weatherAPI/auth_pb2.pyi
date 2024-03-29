from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AuthRequest(_message.Message):
    __slots__ = ["username"]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class AuthResponse(_message.Message):
    __slots__ = ["check"]
    CHECK_FIELD_NUMBER: _ClassVar[int]
    check: bool
    def __init__(self, check: bool = ...) -> None: ...
