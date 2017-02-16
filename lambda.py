"""
Dungeon Assistant
"""

from __future__ import print_function
import random
import json
import urllib
import boto3
from boto3.dynamodb.conditions import Key, Attr

VERSION = 1.0

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Dungeon Assistant. " \
        "You can ask me to roll dice or look up spells. " \
        "You can look up spells by name, like 'Magic Missile'. " \
        "You can also look up by class, level, or both. " \
        "What would you like me to do?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "For instructions on what you can say, please say help me."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Dungeon Assistant. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def handle_session_stop_request():
    card_title = "Stop"
    speech_output = "Ok."
    should_end_session = true
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Functions for the core of Dungeon Assistant  -----------------

def roll_dice(intent, session):
    card_title = "Roll of the Dice"
    session_attributes = {}
    should_end_session = True

    print("roll_dice:", intent['slots'])

    if (not 'value' in intent['slots']['Number']) or (not 'value' in intent['slots']['Sides']):
        speech_output = "You can ask me to roll any number of sided dice like 'Roll 3 die 6.' or 'Roll 2 8 sided dice.'"
        reprompt_text = "You can ask me to roll more dice."
        should_end_session = False
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    try:
        number = int(intent['slots']['Number']['value'])
        sides = int(intent['slots']['Sides']['value'])

        roll_array = []
        natural_twenty_array = []
        tot = 0
        for i in range(0, number):
            roll = int(random.randint(1, sides))
            roll_array.append(roll)
            if sides == 20:
                if roll == 20:
                    natural_twenty_array.append(roll)
            tot += roll

        rolls = "rolls were "
        if number == 1:
            rolls = "roll was "
        roll_array_output = "The " + rolls + (", ").join(map(str, roll_array)) + "."

        dice = "dice"
        if number == 1:
            dice = "die"
        speech_output = "\nI've rolled " + str(number) + " " + dice + " with " + str(sides) + " sides for a total of " + str(tot) +". "
        print("total: " + str(tot))
        speech_output += roll_array_output

        if len(natural_twenty_array) > 0:
            if len(natural_twenty_array) == 1:
                natural_twenty_output = "\nA natural 20! "
            else:
                natural_twenty_output = "\nAlso, there were " + str(len(natural_twenty_array)) + " natural twenties rolled!"

            speech_output += natural_twenty_output
    except Exception as e:
        print("error roll_dice:", e, "Num:" + intent['slots']['Number']['value'], "Sides:" + intent['slots']['Sides']['value'])
        speech_output = "I'm sorry, I had a problem trying to roll the dice you asked for. Could you repeat that?"
        should_end_session = False

    reprompt_text = "" #"You can ask me to roll more dice."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_dynamodb_conn():
    dynamodb = boto3.resource('dynamodb')
    return dynamodb

def get_spell_information_from_dynamo(intent, session):
    card_title = "Spell Information"
    session_attributes = {}
    should_end_session = True

    print("get_spell_info:", intent['slots'])

    if not 'value' in intent['slots']['SpellName']:
        speech_output = "You can look up spells by name, like 'Magic Missile'. " \
                        "You can also look up by class, level, or both. "
        reprompt_text = "" #"You can ask me about another spell."
        should_end_session = False
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    try:
        dynamodb = get_dynamodb_conn()
        spell_book = dynamodb.Table('SpellBook')
        spell_info = ""
        spell_name = (intent['slots']['SpellName']['value']).title()

        spell_name = translate_alexa_to_spellbook_terms(spell_name)

        response = spell_book.get_item(
            Key={
                'spell_name': spell_name
            }
        )
        spell_data = response['Item']
        spell_desc = "Description: " + spell_data['description']
        spell_range = "Range: " + spell_data['range']
        if spell_data['level'] == 0:
            spell_level = "Cantrip"
        else:
            spell_level = "Level: " + str(spell_data['level'])
        spell_casting_time = "Casting time: " + spell_data['casting_time']
        spell_duration = "Duration: " + spell_data['duration']
        spell_components = "Components: " + spell_data['components']
        spell_school = "School: " + spell_data['school']
        spell_classes = "Classes: " + spell_data['classes']
        spell_info = spell_desc + ".\n " + \
                     spell_range + ".\n " + \
                     spell_casting_time  + ".\n " + \
                     spell_duration + ".\n " + \
                     spell_level + ".\n " + \
                     spell_components + ".\n " + \
                     spell_school + ".\n " + \
                     spell_classes

    except Exception as e:
        print("error get_spell_info:", e, "Spell_name:" + spell_name)
        spell_info = " I couldn't find that spell."

    speech_output = spell_name + ". " + spell_info

    reprompt_text = "" #"You can ask me about another spell."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_spells_from_dynamo(intent, session):
    card_title = "Listing spells"
    session_attributes = {}
    should_end_session = True

    print("get_spells:",intent['slots'])

    if (not 'value' in intent['slots']['ClassName']) and (not 'value' in intent['slots']['LevelNumber']) :
        speech_output = "You can look up spells by name, like 'Magic Missile'. " \
                        "You can also look up by class, level, or both. "
        reprompt_text = ""#"You can ask me about another spell."
        should_end_session = False
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    dynamodb = get_dynamodb_conn()
    spell_book = dynamodb.Table('SpellBook')

    class_name = ""
    level_number = -1
    if 'value' in intent['slots']['ClassName']:
        class_name = (intent['slots']['ClassName']['value']).title()
    if 'value' in intent['slots']['LevelNumber']:
        level_number = (intent['slots']['LevelNumber']['value']).title()

    try:
        spells = []
        if class_name != "":
            if level_number == -1:
                spell_list = "Spells for " + class_name + ". "
                response = spell_book.scan(
                    FilterExpression=Attr('classes').contains(class_name)
                )
            else:
                if level_number == "Cantrip" or level_number == "Cantrips":
                    level_number = "0"
                    spell_list = class_name + " cantrips. "
                else:
                    spell_list = "Spells for " + class_name + " level " + level_number + ". "
                response = spell_book.scan(
                    FilterExpression=Attr('classes').contains(class_name) & Attr('level').eq(int(level_number))
                )

            spell_info = response['Items']

            for val in spell_info:
                spells.append((val["spell_name"], val["level"]))

            spells = sorted(spells, key=lambda spell_name: spell_name[0])

            for spell in spells:
                spell_level_number = spell[1]
                if spell[1] == 0:
                    if level_number == "Cantrip" or level_number == "Cantrips" or level_number == "0":
                        spell_list += spell[0] + ".\n "
                    else:
                        spell_list += spell[0] + " cantrip. "
                else:
                    if level_number > -1:
                        spell_list += spell[0] + ".\n "
                    else:
                        spell_list += spell[0] + " Level " + str(spell_level_number) + ".\n "
        else:
            if level_number == "Cantrip" or level_number == "Cantrips":
                spell_level_number = "0"
                spell_list = "Cantrips. "
            else:
                spell_level_number = level_number
                spell_list = "Spells for level " + spell_level_number + ". "
            response = spell_book.scan(
                FilterExpression=Attr('level').eq(int(spell_level_number))
            )

            spell_info = response['Items']

            for val in spell_info:
                spells.append(val["spell_name"])

            spells = sorted(spells)

            for spell in spells:
                spell_list += spell + ".\n "

    except Exception as e:
        print("error get_spells:", e)
        spell_list = " I couldn't find that information."


    speech_output = spell_list

    reprompt_text = "" #"You can ask me about other spells."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def translate_alexa_to_spellbook_terms(spell_name):
    spell_dict = { "Fairy Fire": "Faerie Fire", "Instant Summon": "Drawmij's Instant Summon" }
    spell_name = spell_dict[spell_name]

    return spell_name

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])


    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    print("Version: " + str(VERSION))
    print("intent_name:" + intent_name)

    # Dispatch to your skill's intent handlers
    if intent_name == "RollDiceIntent":
        return roll_dice(intent, session)
    elif intent_name == "WhatSpellIntent":
        return get_spell_information_from_dynamo(intent, session)
    elif intent_name == "ListSpellsIntent":
        return get_spells_from_dynamo(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent":
        return handle_session_end_request()
    elif intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == "VersionIntent":
        return handle_version_intent()
    else:
        raise ValueError("Invalid intent " + intent_name)


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
