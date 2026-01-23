"""
This script builds an exercises table and loads it up with workout data from the free-exercise-db JSON.
"""

import json
import requests
from orama_db_client import OramaDBClient


def fetch_exercises_data():
    """Grab the latest exercise data from GitHub"""
    url = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def create_exercises_table(client):
    """Set up the exercises table with the proper structure"""
    print("Creating exercises table...")
    
    columns = [
        {"name": "id", "type": "INTEGER", "primary_key": True},  # This is the unique ID that auto-increases
        {"name": "name", "type": "TEXT", "nullable": False},
        {"name": "force", "type": "TEXT", "nullable": True},
        {"name": "level", "type": "TEXT", "nullable": True},
        {"name": "mechanic", "type": "TEXT", "nullable": True},
        {"name": "equipment", "type": "TEXT", "nullable": True},
        {"name": "primaryMuscles", "type": "TEXT", "nullable": True},  # We'll store this as a JSON string
        {"name": "secondaryMuscles", "type": "TEXT", "nullable": True},  # We'll store this as a JSON string
        {"name": "instructions", "type": "TEXT", "nullable": True},  # We'll store this as a JSON string
        {"name": "category", "type": "TEXT", "nullable": True},
        {"name": "images", "type": "TEXT", "nullable": True},  # We'll store this as a JSON string with full URLs
        {"name": "original_id", "type": "TEXT", "nullable": True},  # Original id from JSON
        {"name": "status", "type": "INTEGER", "nullable": False, "default": 0}  # Default status = 0
    ]
    
    result = client.create_table(
        table_name="exercises",
        columns=columns
    )
    
    print(f"Table creation result: {result}")
    return result


def populate_exercises(client, exercises_data):
    """Fill the exercises table with data pulled from the JSON"""
    print(f"Inserting {len(exercises_data)} exercises...")
    
    base_image_url = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
    
    success_count = 0
    error_count = 0
    
    for idx, exercise in enumerate(exercises_data, 1):
        try:
            # Build the full URLs for the images
            images = exercise.get('images', [])
            full_image_urls = [base_image_url + img for img in images]
            
            # Get the data ready to insert
            data = {
                "name": exercise.get('name'),
                "force": exercise.get('force'),
                "level": exercise.get('level'),
                "mechanic": exercise.get('mechanic'),
                "equipment": exercise.get('equipment'),
                "primaryMuscles": json.dumps(exercise.get('primaryMuscles', [])),
                "secondaryMuscles": json.dumps(exercise.get('secondaryMuscles', [])),
                "instructions": json.dumps(exercise.get('instructions', [])),
                "category": exercise.get('category'),
                "images": json.dumps(full_image_urls),
                "original_id": exercise.get('id'),
                "status": 0  # All exercises set to status 0
            }
            
            # Add this exercise to the database
            result = client.insert(
                table_name="exercises",
                data=data
            )
            
            # See if it worked - the API gives us a message
            if result.get('message') and 'success' in result.get('message', '').lower():
                success_count += 1
                if idx % 50 == 0:
                    print(f"Progress: {idx}/{len(exercises_data)} exercises inserted...")
            else:
                error_count += 1
                if error_count == 1:  # Show the first error for debugging
                    print(f"\nFirst error response: {result}")
                    print(f"Failed exercise: {exercise.get('name')}\n")
                
        except Exception as e:
            error_count += 1
            if error_count == 1:  # Show the first exception for debugging
                print(f"\nFirst exception: {str(e)}")
                print(f"Failed exercise: {exercise.get('name')}\n")
    
    print(f"\nInsertion complete:")
    print(f"  - Successfully inserted: {success_count}")
    print(f"  - Errors: {error_count}")
    
    return success_count, error_count


def main():
    """The main function that handles creating the table and adding all the exercises"""
    
    # Initialize client
    client = OramaDBClient(
        base_url="https://my-orama.my-domain.com",
        secret_key="orama_db"
    )
    
    print("EXERCISES DATABASE SETUP")
    
    # Step 1: Clean up by removing any existing table
    print("\nStep 1: Cleanup - Delete existing table if present")
    try:
        delete_result = client.delete_table("exercises", confirm=True)
        print(f"Existing table deleted: {delete_result}")
    except Exception as e:
        print(f"No existing table to delete or error: {e}")
    
    # Step 2: Build the exercises table
    print("\nStep 2: Create exercises table")
    create_result = create_exercises_table(client)
    
    if not create_result.get('message') or 'error' in create_result.get('message', '').lower():
        print("Failed to create table. Exiting.")
        return
    
    # Step 3: Grab the exercise data from GitHub
    print("\nStep 3: Fetching exercises data from GitHub...")
    try:
        exercises_data = fetch_exercises_data()
        print(f"Fetched {len(exercises_data)} exercises")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    # Step 4: Fill the table with exercises
    print("\nStep 4: Populating exercises table...")
    success, errors = populate_exercises(client, exercises_data)
    
    # Step 5: Double-check that everything went in correctly
    print("\nStep 5: Verifying data insertion...")
    query_result = client.query("SELECT COUNT(*) as total FROM exercises")
    if query_result.get('results'):
        total = query_result['results'][0]['total']
        print(f"Total exercises in database: {total}")
    
    # Show some sample records
    print("\nSample exercises:")
    sample_query = client.query("SELECT id, name, category, level, status FROM exercises LIMIT 5")
    if sample_query.get('results'):
        print(json.dumps(sample_query.get('results', []), indent=2))
    
    # Show exercises by category
    print("\nExercises count by category:")
    category_query = client.query(
        "SELECT category, COUNT(*) as count FROM exercises GROUP BY category ORDER BY count DESC"
    )
    if category_query.get('results'):
        print(json.dumps(category_query.get('results', []), indent=2))
    
    # Show exercises by status (should all be 0)
    print("\nExercises count by status:")
    status_query = client.query(
        "SELECT status, COUNT(*) as count FROM exercises GROUP BY status"
    )
    if status_query.get('results'):
        print(json.dumps(status_query.get('results', []), indent=2))
    
    print("EXERCISES DATABASE SETUP COMPLETE")


if __name__ == "__main__":
    main()
