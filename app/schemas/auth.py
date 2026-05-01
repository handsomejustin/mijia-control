from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    username = fields.String(required=True, validate=[validate.Length(min=2, max=64)])
    password = fields.String(required=True, validate=[validate.Length(min=6, max=128)])
    email = fields.Email(load_default=None)


class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)


class JwtLoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)
