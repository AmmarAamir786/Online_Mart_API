# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: product.proto
# Protobuf Python Version: 5.27.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    0,
    '',
    'product.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rproduct.proto\"\xdf\x01\n\x07Product\x12\x0f\n\x02id\x18\x01 \x01(\x05H\x00\x88\x01\x01\x12\x11\n\x04name\x18\x02 \x01(\tH\x01\x88\x01\x01\x12\x12\n\x05price\x18\x03 \x01(\x02H\x02\x88\x01\x01\x12\x15\n\x08\x63\x61tegory\x18\x04 \x01(\tH\x03\x88\x01\x01\x12\x18\n\x0b\x64\x65scription\x18\x05 \x01(\tH\x04\x88\x01\x01\x12&\n\toperation\x18\x06 \x01(\x0e\x32\x0e.OperationTypeH\x05\x88\x01\x01\x42\x05\n\x03_idB\x07\n\x05_nameB\x08\n\x06_priceB\x0b\n\t_categoryB\x0e\n\x0c_descriptionB\x0c\n\n_operation*3\n\rOperationType\x12\n\n\x06\x43REATE\x10\x00\x12\n\n\x06UPDATE\x10\x01\x12\n\n\x06\x44\x45LETE\x10\x02\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'product_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_OPERATIONTYPE']._serialized_start=243
  _globals['_OPERATIONTYPE']._serialized_end=294
  _globals['_PRODUCT']._serialized_start=18
  _globals['_PRODUCT']._serialized_end=241
# @@protoc_insertion_point(module_scope)
