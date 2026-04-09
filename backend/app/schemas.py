from marshmallow import Schema, fields, validate

class QuerySchema(Schema):
    disease_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    top_k = fields.Int(load_default=10, validate=validate.Range(min=1, max=20))
    constraints = fields.Dict(keys=fields.Str(), values=fields.Raw(), load_default=dict)

class LoginSchema(Schema):
    email = fields.Email(required=False)
    username = fields.Str(required=False)
    password = fields.Str(required=True)

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True)
