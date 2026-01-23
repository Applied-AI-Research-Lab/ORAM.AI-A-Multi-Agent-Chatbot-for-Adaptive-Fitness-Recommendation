import json

# Load the exercises data
with open('exercises.json', 'r') as f:
    exercises = json.load(f)

# Prompt templates
def get_equipment_for_prompt(ex):
    eq = ex.get('equipment')
    # If equipment is 'other', use the actual value if available, else fallback to 'body only'
    if eq == 'other':
        return ex.get('name')
    return eq or 'body only'

prompt_templates = [
    # Template 1: Simple exercise lookup
    lambda ex: f"Tell me about the {ex.get('name')} exercise",

    # Template 2: Search by muscle group and equipment
    lambda ex: f"What exercise can I do with {get_equipment_for_prompt(ex)} for {(ex.get('primaryMuscles') or ['general fitness'])[0]}?",

    # Template 3: Search by level
    lambda ex: f"Give me a {(ex.get('level') or 'beginner')} exercise for {(ex.get('primaryMuscles') or ['general fitness'])[0]}",

    # Template 4: How to perform
    lambda ex: f"How do I perform the {ex.get('name')} exercise?",

    # Template 5: Search by category
    lambda ex: f"Suggest a {(ex.get('category') or 'strength')} exercise using {get_equipment_for_prompt(ex)}",

    # Template 6: Equipment question
    lambda ex: f"What equipment do I need for {ex.get('name')}?",

    # Template 7: Muscle group question
    lambda ex: f"Which muscles does {ex.get('name')} work?",

    # Template 8: Search by mechanic type
    lambda ex: f"I want a {(ex.get('mechanic') or 'compound')} exercise for {(ex.get('primaryMuscles') or ['general fitness'])[0]}",

    # Template 9: Rehabilitation focus
    lambda ex: f"Show me a rehabilitation exercise for {(ex.get('primaryMuscles') or ['general fitness'])[0]}",

    # Template 10: Exercise instructions
    lambda ex: f"What are the instructions for {ex.get('name')}?",
]

# Open the output file
with open('ft_data.jsonl', 'w') as f:
    for i, ex in enumerate(exercises):
        # Choose two different templates
        template1 = i % 10
        template2 = (i + 1) % 10
        
        # Generate user contents
        user_content1 = prompt_templates[template1](ex)
        user_content2 = prompt_templates[template2](ex)
        
        # Assistant content
        primary_muscles = ', '.join(ex.get('primaryMuscles', []))
        secondary_muscles = ', '.join(ex.get('secondaryMuscles', []))
        muscles = primary_muscles
        if secondary_muscles:
            muscles += f" (secondary: {secondary_muscles})"
        
        assistant_content = f"{ex['name']}\n" + \
                           f"Category: {ex.get('category', 'N/A')}\n" + \
                           f"Level: {ex.get('level', 'N/A')}\n" + \
                           f"Equipment: {ex.get('equipment', 'body only')}\n" + \
                           f"Muscles: {muscles}\n" + \
                           "Instructions:\n" + '\n'.join(f"{i+1}. {instr}" for i, instr in enumerate(ex['instructions']))
        
        # Create the messages
        messages1 = [
            {"role": "system", "content": "You are a specialized rehabilitation and exercise specialist who helps users learn about various exercises. You provide detailed information about each exercise, including step-by-step instructions for proper execution. Your focus is on safe and effective exercise performance for rehabilitation and general fitness."},
            {"role": "user", "content": user_content1},
            {"role": "assistant", "content": assistant_content}
        ]
        
        messages2 = [
            {"role": "system", "content": "You are a specialized rehabilitation and exercise specialist who helps users learn about various exercises. You provide detailed information about each exercise, including step-by-step instructions for proper execution. Your focus is on safe and effective exercise performance for rehabilitation and general fitness."},
            {"role": "user", "content": user_content2},
            {"role": "assistant", "content": assistant_content}
        ]
        
        # Write to file
        f.write(json.dumps({"messages": messages1}) + '\n')
        f.write(json.dumps({"messages": messages2}) + '\n')

print("ft_data.jsonl created successfully.")