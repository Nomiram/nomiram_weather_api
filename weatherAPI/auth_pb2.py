# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: auth.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nauth.proto\x12\x04main\"\x1f\n\x0b\x41uthRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"\x1d\n\x0c\x41uthResponse\x12\r\n\x05\x63heck\x18\x01 \x01(\x08\x32L\n\x0b\x41uthService\x12=\n\x12\x43heckAuthorization\x12\x11.main.AuthRequest\x1a\x12.main.AuthResponse\"\x00\x42\x07Z\x05./;pbb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'auth_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z\005./;pb'
  _AUTHREQUEST._serialized_start=20
  _AUTHREQUEST._serialized_end=51
  _AUTHRESPONSE._serialized_start=53
  _AUTHRESPONSE._serialized_end=82
  _AUTHSERVICE._serialized_start=84
  _AUTHSERVICE._serialized_end=160
# @@protoc_insertion_point(module_scope)
