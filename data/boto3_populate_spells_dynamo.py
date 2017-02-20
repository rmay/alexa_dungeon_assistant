from __future__ import print_function # Python 2/3 compatibility
import boto3
import sqlite3
import json


def get_dynamo_conn():
    return boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")

def create_spell_book_table(db):
    try:
        spellsTable = db.create_table(
            TableName='SpellBook',
            KeySchema=[
                {
                    'AttributeName': 'spell_name',
                    'KeyType': 'HASH'  #Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'spell_name',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )

        return spellsTable

    except Exception as ex:
        print(ex)
        print("Returning existing table")
        return db.Table("SpellBook")

def createSpellEntry(spell_table, spell_info):
    """
    Using the High-Level API, an Item is created and saved to the table.
    Returns True/False depending on the success of the save.
    """

    response = spell_table.put_item(
        Item={
            "spell_name"    : spell_info["spell_name"],
            "level"         : spell_info["level"],
            "casting_time"  : spell_info["casting_time"],
            "components"    : spell_info["components"],
            "description"   : spell_info["description"],
            "duration"      : spell_info["duration"],
            "level"         : spell_info["level"],
            "range"         : spell_info["range"],
            "school"        : spell_info["school"],
            "classes"       : spell_info["classes"]
        }
    )
    print("PutItem succeeded:")
    print(json.dumps(response, indent=4))



def setup_table():
    dbconn = get_dynamo_conn()
    #print(dbconn)
    table = create_spell_book_table(dbconn)
    print(table.table_status)
    return table

def populate_table(spell_info):
    spell_table = setup_table()
    createSpellEntry(spell_table, spell_info)

def connect_to_sqlite():
    return sqlite3.connect('spells.db')

def select_spells_from_sqlite3():
    try:
        conn = connect_to_sqlite()
        curr = conn.execute('SELECT * FROM spells')
        rows = curr.fetchall()

        for row in rows:
            spell_info = {  "spell_name"    : row[1],
                            "casting_time"  : row[2],
                            "components"    : row[3],
                            "description"   : row[4],
                            "duration"      : row[5],
                            "level"         : row[6],
                            "range"         : row[7],
                            "school"        : row[8],
                            "classes"       : row[9] }
            populate_table(spell_info)
    except Exception as ex:
        print("sql error")
        print(ex)

setup_table()
select_spells_from_sqlite3()
