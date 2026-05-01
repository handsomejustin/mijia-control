from marshmallow import Schema, fields, validate


class CreateTokenSchema(Schema):
    name = fields.String(load_default=None, validate=validate.Length(max=64))
    permissions = fields.String(
        load_default="read_write",
        validate=validate.OneOf(["read_only", "read_write"]),
    )
