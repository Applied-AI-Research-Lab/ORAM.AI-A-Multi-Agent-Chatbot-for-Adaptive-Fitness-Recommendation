#!/usr/bin/env python3
"""
TTS Auto-Speak Mode Test Runner
================================

This script runs comprehensive tests of the TTS auto-speak functionality,
measuring both server-side and client-side performance metrics.

Usage:
    python test_autospeak.py --api-url https://my-orama.my-domain.com
    python test_autospeak.py --api-url http://localhost:5000 --delay 2000
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
import subprocess


def load_test_cases():
    """Load test cases from JSON file."""
    test_cases_file = Path(__file__).parent / "test_cases.json"
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_cases'], data['metadata']


def get_test_suite_summary(test_cases):
    """Return summary statistics of the test suite."""
    categories = {}
    total_tests = len(test_cases)
    
    for test in test_cases:
        cat = test['category']
        if cat not in categories:
            categories[cat] = {
                'count': 0,
                'total_words': 0,
                'total_chars': 0
            }
        categories[cat]['count'] += 1
        categories[cat]['total_words'] += test['word_count']
        categories[cat]['total_chars'] += test['char_count']
    
    # Calculate averages
    for cat in categories:
        categories[cat]['avg_words'] = categories[cat]['total_words'] / categories[cat]['count']
        categories[cat]['avg_chars'] = categories[cat]['total_chars'] / categories[cat]['count']
    
    return {
        'total_tests': total_tests,
        'categories': categories,
        'total_words': sum(t['word_count'] for t in test_cases),
        'total_chars': sum(t['char_count'] for t in test_cases),
        'avg_words': sum(t['word_count'] for t in test_cases) / total_tests,
        'avg_chars': sum(t['char_count'] for t in test_cases) / total_tests
    }


# Load test cases
TTS_TEST_CASES, TEST_METADATA = load_test_cases()


def run_client_side_tests(api_url, delay_ms=1000, browser='chrome'):
    """
    Run client-side TTS tests using headless browser.
    
    Args:
        api_url: Base API URL
        delay_ms: Delay between tests in milliseconds
        browser: Browser to use (chrome, firefox)
    
    Returns:
        Path to results file
    """
    print("\n" + "="*70)
    print("CLIENT-SIDE TTS PERFORMANCE TESTING")
    print("="*70)
    print(f"API URL: {api_url}")
    print(f"Test delay: {delay_ms}ms")
    print(f"Browser: {browser}")
    print(f"Total test cases: {len(TTS_TEST_CASES)}")
    print("="*70 + "\n")
    
    # Create HTML test harness
    html_path = Path(__file__).parent / 'tts_test_harness.html'
    results_path = Path(__file__).parent / 'results' / 'tts_client_results.json'
    
    # Ensure results directory exists
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate HTML test file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TTS Auto-Speak Performance Test</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        #progress {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .test-item {{
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #ddd;
            background: #fafafa;
        }}
        .test-item.running {{
            border-left-color: #2196F3;
            background: #E3F2FD;
        }}
        .test-item.success {{
            border-left-color: #4CAF50;
            background: #E8F5E9;
        }}
        .test-item.error {{
            border-left-color: #f44336;
            background: #FFEBEE;
        }}
        #stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2196F3;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
        }}
        button {{
            background: #2196F3;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 5px;
        }}
        button:hover {{
            background: #1976D2;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
    </style>
</head>
<body>
    <h1>TTS Auto-Speak Performance Test</h1>
    
    <div id="progress">
        <div id="status">Ready to start testing...</div>
        <div id="current-test"></div>
        <progress id="progress-bar" max="100" value="0" style="width: 100%; height: 30px; margin-top: 10px;"></progress>
    </div>
    
    <div id="controls">
        <button id="start-btn" onclick="startTests()">Start Tests</button>
        <button id="download-btn" onclick="downloadResults()" disabled>Download Results</button>
        <button id="view-stats-btn" onclick="showStats()" disabled>View Statistics</button>
    </div>
    
    <div id="test-list"></div>
    
    <div id="stats" style="display: none;"></div>

    <script src="tts_performance_monitor.js"></script>
    <script>
        const API_URL = '{api_url}';
        const DELAY_MS = {delay_ms};
        const TEST_CASES = {json.dumps(TTS_TEST_CASES, ensure_ascii=False)};
        
        let monitor = null;
        let testResults = [];
        
        function updateProgress(current, total) {{
            const percentage = (current / total) * 100;
            document.getElementById('progress-bar').value = percentage;
            document.getElementById('status').textContent = 
                `Testing: ${{current}} / ${{total}} (${{percentage.toFixed(1)}}%)`;
        }}
        
        function updateTestItem(testId, status, metrics = null) {{
            const item = document.getElementById(`test-${{testId}}`);
            if (!item) return;
            
            item.className = `test-item ${{status}}`;
            
            if (metrics && metrics.success) {{
                item.innerHTML += ` - Success ${{metrics.total_time_to_audio_ms.toFixed(0)}}ms`;
            }} else if (status === 'error') {{
                item.innerHTML += ` - Failed`;
            }}
        }}
        
        async function startTests() {{
            document.getElementById('start-btn').disabled = true;
            document.getElementById('download-btn').disabled = true;
            document.getElementById('view-stats-btn').disabled = true;
            
            // Initialize monitor
            monitor = new TTSPerformanceMonitor(API_URL, false);
            
            // Create test list UI
            const testList = document.getElementById('test-list');
            testList.innerHTML = '<h2>Test Progress</h2>';
            TEST_CASES.forEach(tc => {{
                const div = document.createElement('div');
                div.id = `test-${{tc.id}}`;
                div.className = 'test-item';
                div.textContent = `#${{tc.id}}: ${{tc.description}} (${{tc.category}}, ${{tc.word_count}} words)`;
                testList.appendChild(div);
            }});
            
            // Run tests
            try {{
                testResults = await monitor.runTestSuite(TEST_CASES, DELAY_MS, 
                    (current, total, result) => {{
                        updateProgress(current, total);
                        updateTestItem(result.test_id, result.success ? 'success' : 'error', result);
                    }}
                );
                
                document.getElementById('status').textContent = 'All tests completed!';
                document.getElementById('download-btn').disabled = false;
                document.getElementById('view-stats-btn').disabled = false;
                
                // Auto-show stats
                showStats();
                
                // Auto-download results
                monitor.downloadResults('tts_client_results_' + new Date().getTime() + '.json');
                
            }} catch (error) {{
                document.getElementById('status').textContent = 'Test error: ' + error.message;
                console.error('Test execution error:', error);
            }}
        }}
        
        function downloadResults() {{
            if (monitor) {{
                monitor.downloadResults('tts_client_results_' + new Date().getTime() + '.json');
            }}
        }}
        
        function showStats() {{
            if (!monitor) return;
            
            const stats = monitor.getSummaryStats();
            const statsDiv = document.getElementById('stats');
            statsDiv.style.display = 'block';
            
            statsDiv.innerHTML = `
                <h2>Performance Statistics</h2>
                <div class="metric">
                    <div class="metric-value">${{stats.total_tests}}</div>
                    <div class="metric-label">Total Tests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{stats.successful_tests}}</div>
                    <div class="metric-label">Successful</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{stats.success_rate}}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{stats.total_time_to_audio_ms?.mean || 'N/A'}}ms</div>
                    <div class="metric-label">Avg Time to Audio</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{stats.network_request_duration_ms?.mean || 'N/A'}}ms</div>
                    <div class="metric-label">Avg Network Time</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{stats.audio_duration_seconds?.mean || 'N/A'}}s</div>
                    <div class="metric-label">Avg Audio Duration</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{stats.blob_size_kb?.mean || 'N/A'}}KB</div>
                    <div class="metric-label">Avg File Size</div>
                </div>
            `;
        }}
        
        // NOTE: Auto-start is disabled to allow user interaction for browser autoplay policy
        // User must click "Start Tests" button to begin
        // setTimeout(() => {{
        //     console.log('Auto-starting tests in headless mode...');
        //     startTests();
        // }}, 2000);
    </script>
</body>
</html>
""")
    
    print(f"Test harness created: {html_path}")
    print(f"Results will be saved to: {results_path}")
    print("\nYou can run this test by:")
    print(f"1. Opening {html_path} in a browser, OR")
    print(f"2. Running with Playwright/Puppeteer (automated)")
    print("\nFor now, please open the HTML file manually and the results will auto-download.")
    print("\nPress ENTER when tests are complete...")
    input()
    
    return results_path


def analyze_results(client_results_path, server_results_path=None):
    """
    Analyze test results and generate summary statistics.
    
    Args:
        client_results_path: Path to client-side results JSON
        server_results_path: Path to server-side results JSONL (optional)
    
    Returns:
        Dictionary of analysis results
    """
    print("\n" + "="*70)
    print("ANALYZING TEST RESULTS")
    print("="*70 + "\n")
    
    # Load client results
    with open(client_results_path, 'r') as f:
        client_results = json.load(f)
    
    print(f"Loaded {len(client_results)} client-side test results")
    
    # Load server results if available
    server_results = []
    if server_results_path and Path(server_results_path).exists():
        with open(server_results_path, 'r') as f:
            server_results = [json.loads(line) for line in f if line.strip()]
        print(f"Loaded {len(server_results)} server-side test results")
    
    # Analyze by category
    categories = {}
    for result in client_results:
        if not result.get('success'):
            continue
            
        cat = result.get('category', 'unknown')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)
    
    # Print summary
    print(f"\nResults by Category:")
    print("-" * 70)
    
    for cat, results in sorted(categories.items()):
        if not results:
            continue
            
        times = [r['total_time_to_audio_ms'] for r in results if 'total_time_to_audio_ms' in r]
        network = [r['network_request_duration_ms'] for r in results if 'network_request_duration_ms' in r]
        audio_dur = [r['audio_duration_seconds'] for r in results if 'audio_duration_seconds' in r]
        
        if times:
            print(f"\n{cat.upper()}:")
            print(f"  Tests: {len(results)}")
            print(f"  Avg Time to Audio: {sum(times)/len(times):.1f}ms")
            print(f"  Avg Network Time: {sum(network)/len(network):.1f}ms" if network else "")
            print(f"  Avg Audio Duration: {sum(audio_dur)/len(audio_dur):.2f}s" if audio_dur else "")
    
    return {
        'client_results': client_results,
        'server_results': server_results,
        'categories': categories
    }


def main():
    parser = argparse.ArgumentParser(description='Test TTS Auto-Speak Performance')
    parser.add_argument('--api-url', default='https://my-orama.my-domain.com',
                       help='Base API URL')
    parser.add_argument('--delay', type=int, default=1000,
                       help='Delay between tests in milliseconds')
    parser.add_argument('--browser', default='chrome',
                       choices=['chrome', 'firefox'],
                       help='Browser to use for testing')
    parser.add_argument('--skip-client', action='store_true',
                       help='Skip client-side tests')
    parser.add_argument('--analyze-only', type=str,
                       help='Path to existing results file to analyze')
    
    args = parser.parse_args()
    
    # Print test suite summary
    summary = get_test_suite_summary(TTS_TEST_CASES)
    print("\n" + "="*70)
    print("TTS AUTO-SPEAK PERFORMANCE TEST SUITE")
    print("="*70)
    print(f"Total test cases: {summary['total_tests']}")
    print(f"Total words: {summary['total_words']}")
    print(f"Total characters: {summary['total_chars']}")
    print(f"Average words per test: {summary['avg_words']:.1f}")
    print(f"Average characters per test: {summary['avg_chars']:.1f}")
    print("\nTest Distribution by Category:")
    for cat, stats in summary['categories'].items():
        print(f"  • {cat.capitalize()}: {stats['count']} tests "
              f"(avg {stats['avg_words']:.0f} words)")
    print("="*70)
    
    # Run tests or analyze existing results
    if args.analyze_only:
        analyze_results(args.analyze_only)
    else:
        if not args.skip_client:
            results_path = run_client_side_tests(args.api_url, args.delay, args.browser)
            print(f"\nClient-side testing complete!")
            print(f"Results saved to: {results_path}")
        
        print("\nAll tests complete!")


if __name__ == '__main__':
    main()
