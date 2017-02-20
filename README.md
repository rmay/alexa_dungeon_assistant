# Alexa Skill Dungeon Assistant
Code for my Alexa Skill Dungeon Assistant

**Usage**

The Alexa Skill calls lambda.py

**Testing locally**

I haven't figured out how to do CI testing with Alexa Skills and Python code. `emulambda` has worked just fine for local manual testing.


Install emulambda. `pip install -e emulambda`
See https://github.com/fugue/emulambda for more information

Run emulambda

`emulambda lambda.lambda_handler testjson/dicetest2.json`

Add `-v` for more information.

`emulambda lambda.lambda_handler testjson/dicetest2.json -v`


**Spell Book Data**

Run `boto3_populate_spells_dynamo.py` insert the spells in `spell.db` into your DynamoDB. The default is to a local instance of DynamoDB.


**Requirements**

- Python 2.7
- emulambda
- AWS account with credentials on your development machine
- Alexa Developer account
- DynamoDB configured and loaded with the D&D 5e spells.
