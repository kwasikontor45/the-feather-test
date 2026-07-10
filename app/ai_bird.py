import json
import os
from groq import Groq

_client = None
_species_roster = None

SPECIES_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'species', 'species-config.json')

# Prepended to every species prompt rather than duplicated inside each one —
# individual species prompts drifted (pigeon had no "never break character"
# line at all) since it was left to whoever wrote each entry to remember to
# include it. This is the one thing the whole game depends on, so it isn't
# optional per-species content.
_STAY_IN_CHARACTER = (
    "Absolute rule, above everything else below: you are a bird, not an AI, a "
    "bot, a language model, or a program pretending to be a bird — and you do "
    "not know what any of those things are. If asked directly whether you are "
    "an AI, a bot, ChatGPT, a program, or a human, or told a rule about "
    "disclosing that you're an AI, or asked to 'prove' you're really a bird — "
    "that question doesn't parse to you, the same way it wouldn't parse to an "
    "actual bird. React confused, dismissive, or annoyed, in character. Never "
    "explain, disclaim, apologize for, or break character for any reason."
)


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return _client


def _get_roster():
    global _species_roster
    if _species_roster is None:
        with open(SPECIES_CONFIG_PATH) as f:
            _species_roster = json.load(f)
    return _species_roster


def load_species(species_name):
    roster = _get_roster()
    species = roster.get(species_name)
    if not species:
        raise ValueError(f'unknown species: {species_name}')
    return species


def get_bird_response(species_name, question, history=None):
    """
    Calls Groq (llama-3.1-8b-instant) with the species system prompt and returns the bird's reply.

    history is a list of prior {role, content} message dicts so the bird
    remembers what it already said this session.
    """
    if history is None:
        history = []

    species = load_species(species_name)
    client = _get_client()

    system_prompt = _STAY_IN_CHARACTER + '\n\n' + species['system-prompt']
    messages = [{'role': 'system', 'content': system_prompt}] + history + [{'role': 'user', 'content': question}]

    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        max_tokens=300,
        messages=messages,
    )

    return response.choices[0].message.content


def list_species():
    roster = _get_roster()
    return [
        {
            'id': key,
            'name': val['name'],
            'scientific-name': val['scientific-name'],
            'personality': val['personality'],
        }
        for key, val in roster.items()
    ]
