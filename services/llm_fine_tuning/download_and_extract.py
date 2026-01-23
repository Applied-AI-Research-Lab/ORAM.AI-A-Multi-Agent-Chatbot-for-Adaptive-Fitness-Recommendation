"""
Script to download all exercises from the free-exercise-db
and save them to a JSON file.
"""

import requests
import json
from typing import List, Dict, Any


def fetch_exercises() -> List[Dict[str, Any]]:
    """
    Downloads all exercises from the free-exercise-db GitHub repository.
    
    Returns:
        List[Dict[str, Any]]: List of all exercises
    """
    url = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
    
    print(f"Downloading data from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        exercises = response.json()
        print(f"✓ Successfully fetched {len(exercises)} exercises")
        
        return exercises
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Error while fetching data: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"✗ Error while reading JSON: {e}")
        raise


def enrich_exercises_with_images(exercises: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Adds full URLs for the exercise images.
    
    Args:
        exercises: List of exercises
        
    Returns:
        List[Dict[str, Any]]: Exercises with full image URLs
    """
    base_image_url = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
    
    for exercise in exercises:
        if 'images' in exercise and exercise['images']:
            # Add full URLs
            exercise['image_urls'] = [
                f"{base_image_url}{img_path}" 
                for img_path in exercise['images']
            ]
    
    return exercises


def save_exercises_to_json(exercises: List[Dict[str, Any]], filename: str = "exercises.json") -> None:
    """
    Saves the exercises to a JSON file.
    
    Args:
        exercises: List of exercises
        filename: File name (default: exercises.json)
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(exercises, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Exercises saved to file: {filename}")
        print(f"  File size: {len(json.dumps(exercises)) / 1024:.2f} KB")
        
    except IOError as e:
        print(f"✗ Error while saving: {e}")
        raise


def print_exercise_statistics(exercises: List[Dict[str, Any]]) -> None:
    """
    Displays statistics for the exercises.
    
    Args:
        exercises: List of exercises
    """
    print("\n" + "="*60)
    print("EXERCISE STATISTICS")
    print("="*60)
    
    # Total number of exercises
    print(f"Total exercises: {len(exercises)}")
    
    # Categories
    categories = {}
    for ex in exercises:
        cat = ex.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\nCategories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count}")
    
    # Difficulty levels
    levels = {}
    for ex in exercises:
        level = ex.get('level', 'Unknown')
        levels[level] = levels.get(level, 0) + 1
    
    print(f"\nDifficulty levels:")
    for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {level}: {count}")
    
    # Equipment
    equipment = {}
    for ex in exercises:
        eq = ex.get('equipment', 'Unknown')
        equipment[eq] = equipment.get(eq, 0) + 1
    
    print(f"\nEquipment (Top 10):")
    for eq, count in sorted(equipment.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {eq}: {count}")
    
    # Primary muscles
    primary_muscles = {}
    for ex in exercises:
        for muscle in ex.get('primaryMuscles', []):
            primary_muscles[muscle] = primary_muscles.get(muscle, 0) + 1
    
    print(f"\nPrimary muscles:")
    for muscle, count in sorted(primary_muscles.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {muscle}: {count}")
    
    print("="*60 + "\n")


def main():
    """Main function of the script."""
    print("\n" + "="*60)
    print("FREE EXERCISE DB - EXTRACTION SCRIPT")
    print("="*60 + "\n")
    
    # Download exercises
    exercises = fetch_exercises()
    
    # Enrich with image URLs
    exercises = enrich_exercises_with_images(exercises)
    
    # Show statistics
    print_exercise_statistics(exercises)
    
    # Save to JSON
    save_exercises_to_json(exercises)
    
    # Show example exercise
    if exercises:
        print("\nExample exercise:")
        print("-" * 60)
        example = exercises[0]
        print(f"ID: {example.get('id')}")
        print(f"Name: {example.get('name')}")
        print(f"Category: {example.get('category')}")
        print(f"Level: {example.get('level')}")
        print(f"Equipment: {example.get('equipment')}")
        print(f"Primary muscles: {', '.join(example.get('primaryMuscles', []))}")
        if 'image_urls' in example:
            print(f"Images: {len(example.get('image_urls', []))}")
        print("-" * 60)
    
    print("\n✓ Completed successfully!\n")


if __name__ == "__main__":
    main()
