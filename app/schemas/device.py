from marshmallow import Schema, fields


class SetPropertySchema(Schema):
    value = fields.Raw(required=True)


class RunActionSchema(Schema):
    value = fields.Raw(load_default=None)
