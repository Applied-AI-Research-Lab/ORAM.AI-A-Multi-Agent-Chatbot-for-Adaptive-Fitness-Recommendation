"""
Baseline Comparison
This version creates results by running the same test cases through both controllers.].
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path


class BaselineTester:
    """Handles baseline comparison testing with the current server configuration"""
    
    def __init__(self, base_url="https://my-orama.my-domain.com"):
        self.base_url = base_url
        
    def load_test_cases(self):
        """Load test cases from the existing test suite"""
        test_path = Path(__file__).parent.parent / "chatbot-testing" / "test_cases.json"
        with open(test_path, 'r') as f:
            test_data = json.load(f)
        
        # Flatten all categories
        all_cases = []
        for category in test_data.values():
            all_cases.extend(category)
        
        return all_cases
    
    def run_comparison(self, num_tests=10):
        """
        Run a comparison on first N test cases.

        Args:
            num_tests: Number of test cases to run (default 10 for test)
        """
        print("-"*80)
        print("BASELINE COMPARISON")
        print("-"*80)
        
        test_cases = self.load_test_cases()[:num_tests]
        
        print(f"\nTesting {len(test_cases)} cases")
        print("\nCurrent Configuration Check:")
        print("Please verify which controller is active in app.py /chat route:")
        print("  - Option 1: chat_controller.chat() [Single-LLM]")
        print("  - Option 2: agentic_controller.chat() [Multi-Agent]")
        
        config_type = input("\nWhich is currently active? (1 for Single-LLM, 2 for Multi-Agent): ")
        
        if config_type == "1":
            output_file = "single_llm_results.json"
            print("\nRunning tests on Single-LLM Baseline...")
        elif config_type == "2":
            output_file = "multi_agent_results.json"
            print("\nRunning tests on Multi-Agent System...")
        else:
            print("Invalid choice. Exiting.")
            return
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Testing: {test_case.get('message', '')[:60]}...")
            
            url = f"{self.base_url}/chat"
            headers = {
                "Authorization": "Bearer secret_key_for_testing",
                "Content-Type": "application/json"
            }
            payload = {
                "userKey": f"baseline_test_{config_type}",
                "message": test_case.get('message', ''),
                "stealthMode": True
            }
            
            start_time = time.time()
            
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Extract metrics
                    agent_logs = response_data.get('agent_logs', [])
                    agents_used = [log.get('agent') for log in agent_logs]
                    
                    # Analyze agent execution
                    is_exercise_related = False
                    keyword_extracted = None
                    exercises_found = 0
                    
                    for log in agent_logs:
                        if 'Agent1' in log.get('agent', ''):
                            output = log.get('output', {})
                            is_exercise_related = output.get('is_exercise_related', False)
                            keyword_extracted = output.get('keyword')
                        elif 'MCP' in log.get('agent', ''):
                            output = log.get('output', {})
                            exercises_found = output.get('count', 0)
                    
                    result = {
                        "test_id": test_case.get('id'),
                        "message": test_case.get('message'),
                        "category": test_case.get('expected_category'),
                        "response_time": round(end_time - start_time, 3),
                        "response_text": response_data.get('response', ''),
                        "response_length": len(response_data.get('response', '')),
                        "word_count": len(response_data.get('response', '').split()),
                        "agents_used": agents_used,
                        "is_exercise_related": is_exercise_related,
                        "keyword_extracted": keyword_extracted,
                        "exercises_found": exercises_found,
                        "status": "success"
                    }
                    
                    print(f"  Success - {result['response_time']}s")
                    if agents_used:
                        print(f"     Agents: {', '.join(agents_used)}")
                    
                else:
                    result = {
                        "test_id": test_case.get('id'),
                        "message": test_case.get('message'),
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }
                    print(f"  Error: HTTP {response.status_code}")
                
                results.append(result)
                time.sleep(0.5)  # Brief pause to avoid rate limiting
                
            except Exception as e:
                print(f"  Exception: {str(e)}")
                results.append({
                    "test_id": test_case.get('id'),
                    "message": test_case.get('message'),
                    "status": "error",
                    "error": str(e)
                })
        
        # Save results to file
        output_path = Path(__file__).parent / "results" / output_file
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'-'*80}")
        print(f"Results saved to: {output_path}")
        print(f"{'-'*80}")
        
        # Print summary
        success_count = sum(1 for r in results if r.get('status') == 'success')
        if success_count > 0:
            avg_time = sum(r.get('response_time', 0) for r in results if r.get('status') == 'success') / success_count
            print(f"\nSuccess rate: {success_count}/{len(results)}")
            print(f"Average response time: {avg_time:.3f}s")
            
            if config_type == "2":
                exercise_count = sum(1 for r in results if r.get('is_exercise_related'))
                print(f"Exercise-related queries: {exercise_count}/{len(results)}")


if __name__ == "__main__":
    tester = BaselineTester()
    
    print("\nOptions:")
    print("1. Test (10 cases)")
    print("2. Full test (all 25 cases)")
    
    choice = input("Select option (1 or 2): ")
    
    if choice == "1":
        tester.run_comparison(num_tests=10)
    else:
        tester.run_comparison(num_tests=25)