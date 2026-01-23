"""
Comprehensive Chatbot Testing Suite
Tests multi-agent system with detailed performance metrics
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import statistics


class ChatbotTester:
    """Comprehensive testing framework for ORAMA chatbot"""
    
    def __init__(self, base_url="https://my-orama.my-domain.com"):
        """
        Initialize tester.
        
        Args:
            base_url: Base URL of the chatbot API
        """
        self.base_url = base_url
        self.results = []
        self.test_start_time = None
    
    def _analyze_agent_logs(self, logs):
        """
        Analyze agent logs to extract execution patterns.
        
        Args:
            logs: List of agent log entries
            
        Returns:
            dict: Analyzed agent execution information
        """
        if not logs:
            return {
                'agents_used': [],
                'is_exercise_related': False,
                'keyword_extracted': None,
                'exercises_found': 0,
                'agent_count': 0,
                'execution_flow': []
            }
        
        analysis = {
            'agents_used': [],
            'is_exercise_related': False,
            'keyword_extracted': None,
            'exercises_found': 0,
            'agent_count': len(logs),
            'execution_flow': [],
            'agent1_reasoning': None,
            'agent2_suggestions_preview': None,
            'mcp_time_ms': None,
            'mcp_success': None,
            'mcp_exercises_summary': []
        }
        
        for log in logs:
            agent_name = log.get('agent', 'Unknown')
            analysis['agents_used'].append(agent_name)
            analysis['execution_flow'].append({
                'agent': agent_name,
                'timestamp': log.get('timestamp', '')
            })
            
            # Extract specific information from each agent
            if 'Agent1' in agent_name:
                output = log.get('output', {})
                analysis['is_exercise_related'] = output.get('is_exercise_related', False)
                analysis['keyword_extracted'] = output.get('keyword')
                analysis['agent1_reasoning'] = output.get('reasoning', '')
            
            elif 'MCP' in agent_name:
                output = log.get('output', {})
                analysis['exercises_found'] = output.get('count', 0)
                analysis['mcp_time_ms'] = output.get('mcp_time_ms')
                analysis['mcp_success'] = output.get('success', False)
                analysis['mcp_exercises_summary'] = output.get('exercises_summary', [])
            
            elif 'Agent2' in agent_name:
                output = log.get('output', {})
                suggestions = output.get('suggestions', '')
                analysis['agent2_suggestions_preview'] = suggestions[:200] if suggestions else None
        
        return analysis
        
    def run_single_test(self, test_case, user_key="test_user_performance"):
        """
        Run a single test case and measure performance.
        
        Args:
            test_case: Test case dictionary
            user_key: User key for session tracking
            
        Returns:
            dict: Test results with timing and response data
        """
        test_id = test_case.get('id', 'unknown')
        message = test_case.get('message', '')
        
        print(f"\n{'='*60}")
        print(f"Running Test: {test_id} - {test_case.get('description', 'No description')}")
        print(f"Message: '{message}'")
        print(f"{'='*60}")
        
        # Prepare request
        url = f"{self.base_url}/chat"
        headers = {
            "Authorization": "Bearer YOUR_API_KEY_HERE",
            "Content-Type": "application/json"
        }
        payload = {
            "userKey": user_key,
            "message": message
        }
        
        # Measure total request time
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            end_time = time.time()
            
            total_time = end_time - start_time
            
            # Parse response
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract agent logs and analyze them
                agent_logs = response_data.get('agent_logs', [])
                agent_analysis = self._analyze_agent_logs(agent_logs)
                
                result = {
                    "test_id": test_id,
                    "timestamp": datetime.now().isoformat(),
                    "category": test_case.get('expected_category', 'unknown'),
                    "message": message,
                    "description": test_case.get('description', ''),
                    "status": "success",
                    "status_code": response.status_code,
                    "total_response_time": round(total_time, 3),
                    "response_text": response_data.get('response', ''),
                    "response_length": len(response_data.get('response', '')),
                    "expected_category": test_case.get('expected_category'),
                    "expected_keyword": test_case.get('expected_keyword'),
                    # Agent execution information
                    "agent_logs": agent_logs,
                    "agent_analysis": agent_analysis,
                    "agents_used": agent_analysis.get('agents_used', []),
                    "is_exercise_related": agent_analysis.get('is_exercise_related', False),
                    "keyword_extracted": agent_analysis.get('keyword_extracted'),
                    "exercises_found": agent_analysis.get('exercises_found', 0),
                    "execution_flow": agent_analysis.get('execution_flow', []),
                    # MCP-specific statistics
                    "mcp_time_ms": agent_analysis.get('mcp_time_ms'),
                    "mcp_success": agent_analysis.get('mcp_success'),
                    "mcp_exercises_summary": agent_analysis.get('mcp_exercises_summary', []),
                    "raw_response": response_data
                }
                
                print(f"SUCCESS")
                print(f"Total Time: {total_time:.3f}s")
                print(f"Agents Used: {', '.join(agent_analysis.get('agents_used', []))}")
                if agent_analysis.get('is_exercise_related'):
                    print(f"Exercise Keyword: {agent_analysis.get('keyword_extracted')}")
                    print(f"Exercises Found: {agent_analysis.get('exercises_found')}")
                    if agent_analysis.get('mcp_time_ms'):
                        print(f"MCP Time: {agent_analysis.get('mcp_time_ms')}ms")
                print(f"Response: {response_data.get('response', '')[:100]}...")
                
            else:
                result = {
                    "test_id": test_id,
                    "timestamp": datetime.now().isoformat(),
                    "category": test_case.get('expected_category', 'unknown'),
                    "message": message,
                    "description": test_case.get('description', ''),
                    "status": "error",
                    "status_code": response.status_code,
                    "total_response_time": round(total_time, 3),
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text
                }
                
                print(f"ERROR: HTTP {response.status_code}")
                
        except requests.Timeout:
            result = {
                "test_id": test_id,
                "timestamp": datetime.now().isoformat(),
                "category": test_case.get('expected_category', 'unknown'),
                "message": message,
                "description": test_case.get('description', ''),
                "status": "timeout",
                "total_response_time": 60.0,
                "error": "Request timeout after 60s"
            }
            print(f"TIMEOUT: Request exceeded 60s")
            
        except Exception as e:
            result = {
                "test_id": test_id,
                "timestamp": datetime.now().isoformat(),
                "category": test_case.get('expected_category', 'unknown'),
                "message": message,
                "description": test_case.get('description', ''),
                "status": "exception",
                "error": str(e)
            }
            print(f"EXCEPTION: {str(e)}")
        
        return result
    
    def run_all_tests(self, test_cases_file="testing/chatbot-testing/test_cases.json"):
        """
        Run all test cases from JSON file.
        
        Args:
            test_cases_file: Path to test cases JSON file
            
        Returns:
            list: All test results
        """
        print("\n" + "="*70)
        print("STARTING COMPREHENSIVE CHATBOT TESTS")
        print("="*70)
        
        self.test_start_time = datetime.now()
        
        # Load test cases
        with open(test_cases_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        all_tests = []
        
        # Flatten all test categories
        for category, tests in test_data.items():
            for test in tests:
                test['test_category'] = category
                all_tests.append(test)
        
        print(f"\nTotal tests to run: {len(all_tests)}")
        print(f"   - General questions: {len(test_data.get('general_questions', []))}")
        print(f"   - Exercise questions: {len(test_data.get('exercise_questions', []))}")
        print(f"   - Edge cases: {len(test_data.get('edge_cases', []))}")
        
        # Run each test
        for i, test_case in enumerate(all_tests, 1):
            print(f"\n[{i}/{len(all_tests)}]", end=" ")
            result = self.run_single_test(test_case)
            self.results.append(result)
            
            # Small delay between tests
            time.sleep(0.5)
        
        self.test_end_time = datetime.now()
        
        return self.results
    
    def save_results(self, output_file="testing/chatbot-testing/results/test_results.json"):
        """Save test results to JSON file."""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "test_run_metadata": {
                "start_time": self.test_start_time.isoformat() if self.test_start_time else None,
                "end_time": self.test_end_time.isoformat() if self.test_end_time else None,
                "total_tests": len(self.results),
                "base_url": self.base_url
            },
            "results": self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print test summary statistics."""
        if not self.results:
            print("No results to summarize")
            return
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('status') == 'success')
        errors = sum(1 for r in self.results if r.get('status') == 'error')
        timeouts = sum(1 for r in self.results if r.get('status') == 'timeout')
        exceptions = sum(1 for r in self.results if r.get('status') == 'exception')
        
        # Calculate timing statistics
        response_times = [r['total_response_time'] for r in self.results if 'total_response_time' in r]
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nOverall Results:")
        print(f"   Total Tests: {total}")
        print(f"   Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"   Errors: {errors} ({errors/total*100:.1f}%)")
        print(f"   Timeouts: {timeouts} ({timeouts/total*100:.1f}%)")
        print(f"   Exceptions: {exceptions} ({exceptions/total*100:.1f}%)")
        
        if response_times:
            print(f"\nResponse Time Statistics:")
            print(f"   Mean: {statistics.mean(response_times):.3f}s")
            print(f"   Median: {statistics.median(response_times):.3f}s")
            print(f"   Min: {min(response_times):.3f}s")
            print(f"   Max: {max(response_times):.3f}s")
            if len(response_times) > 1:
                print(f"   Std Dev: {statistics.stdev(response_times):.3f}s")
        
        # Category breakdown
        general_tests = [r for r in self.results if r.get('category') == 'general']
        exercise_tests = [r for r in self.results if r.get('category') == 'exercise']
        
        if general_tests:
            general_success = sum(1 for r in general_tests if r.get('status') == 'success')
            general_times = [r['total_response_time'] for r in general_tests if 'total_response_time' in r]
            print(f"\nGeneral Questions ({len(general_tests)} tests):")
            print(f"   Success Rate: {general_success/len(general_tests)*100:.1f}%")
            if general_times:
                print(f"   Avg Response Time: {statistics.mean(general_times):.3f}s")
        
        if exercise_tests:
            exercise_success = sum(1 for r in exercise_tests if r.get('status') == 'success')
            exercise_times = [r['total_response_time'] for r in exercise_tests if 'total_response_time' in r]
            print(f"\nExercise Questions ({len(exercise_tests)} tests):")
            print(f"   Success Rate: {exercise_success/len(exercise_tests)*100:.1f}%")
            if exercise_times:
                print(f"   Avg Response Time: {statistics.mean(exercise_times):.3f}s")
        
        print("\n" + "="*70)


def main():
    """Main test execution function."""
    # Initialize tester
    tester = ChatbotTester(base_url="https://my-orama.my-domain.com")
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results
    tester.save_results()
    
    # Print summary
    tester.print_summary()
    
    print("\nTesting complete!")


if __name__ == "__main__":
    main()
