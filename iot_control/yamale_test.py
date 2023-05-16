# Import Yamale and make a schema object:
import yamale
schema = yamale.make_schema('schema.yaml')
data = yamale.make_data('../garden_defekt.yaml')
# Validate data against the schema. Throws a ValueError if data is invalid.
yamale.validate(schema, data)
