#!/usr/bin/env python3
"""
Voice Input (Speech-to-Text) Test Runner
=========================================

This script runs comprehensive tests of the voice input functionality,
measuring transcription accuracy and performance metrics.

Usage:
    python test_voice_input.py --api-url https://my-orama.my-domain.com
    python test_voice_input.py --api-url http://localhost:5000
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


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
    total_words = sum(tc['word_count'] for tc in test_cases)
    total_chars = sum(tc['char_count'] for tc in test_cases)
    
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
        count = categories[cat]['count']
        categories[cat]['avg_words'] = categories[cat]['total_words'] / count
        categories[cat]['avg_chars'] = categories[cat]['total_chars'] / count
    
    return {
        'total_tests': total_tests,
        'total_words': total_words,
        'total_chars': total_chars,
        'avg_words': total_words / total_tests,
        'avg_chars': total_chars / total_tests,
        'categories': categories
    }


def generate_test_harness(api_url, test_cases):
    """Generate HTML test harness for voice input testing."""
    
    test_harness_path = Path(__file__).parent / "voice_test_harness.html"
    results_path = Path(__file__).parent / "results" / "stt_results.json"
    
    # Ensure results directory exists
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = f"""<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speech-to-Text (STT) Performance Test</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        #controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        button {{
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }}
        #start-btn {{
            background: #667eea;
            color: white;
        }}
        #start-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
        }}
        #record-btn {{
            background: #f44336;
            color: white;
        }}
        #record-btn:hover {{
            background: #da190b;
        }}
        #record-btn.recording {{
            background: #ff5252;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        #download-btn {{
            background: #4CAF50;
            color: white;
        }}
        #download-btn:hover {{
            background: #45a049;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }}
        #progress {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        #status {{
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 15px;
        }}
        #test-display {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            min-height: 100px;
        }}
        #test-display.active {{
            background: #d4edda;
            border-color: #28a745;
        }}
        #current-text {{
            font-size: 24px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.6;
        }}
        #test-info {{
            font-size: 14px;
            color: #666;
        }}
        #transcription-result {{
            background: #e3f2fd;
            border: 2px solid #2196F3;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            display: none;
        }}
        #transcription-result.show {{
            display: block;
        }}
        .accuracy {{
            font-size: 16px;
            font-weight: 600;
            margin-top: 10px;
        }}
        .accuracy.good {{ color: #4CAF50; }}
        .accuracy.warning {{ color: #FF9800; }}
        .accuracy.poor {{ color: #f44336; }}
        #results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        #results-table th, #results-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        #results-table th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        #results-table tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .test-row.success {{
            background: #d4edda;
        }}
        .test-row.error {{
            background: #f8d7da;
        }}
        #stats {{
            display: none;
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        #stats.show {{
            display: block;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Speech-to-Text (STT) Performance Test</h1>
        <p class="subtitle">Transcription Accuracy & Latency Evaluation</p>
        
        <div id="controls">
            <button id="start-btn" onclick="startTests()">Start Testing Session</button>
            <button id="record-btn" onclick="toggleRecording()" disabled>🎤 Record</button>
            <button id="download-btn" onclick="downloadResults()" disabled>💾 Download Results</button>
        </div>
        
        <div id="progress">
            <div id="status">Ready to start</div>
            <div id="progress-text">Test 0 of {len(test_cases)}</div>
        </div>
        
        <div id="test-display">
            <div id="test-info">Click "Start Testing Session" to begin</div>
            <div id="current-text"></div>
            <div id="transcription-result">
                <strong>Transcription:</strong>
                <div id="transcription-text"></div>
                <div class="accuracy" id="accuracy-display"></div>
            </div>
        </div>
        
        <div id="stats">
            <h2>📊 Test Results Summary</h2>
            <div id="stats-content"></div>
        </div>
        
        <table id="results-table" style="display:none;">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Category</th>
                    <th>Original Text</th>
                    <th>Transcription</th>
                    <th>Accuracy</th>
                    <th>Time (ms)</th>
                </tr>
            </thead>
            <tbody id="results-tbody"></tbody>
        </table>
    </div>

    <script>
        const API_URL = '{api_url}';
        const TEST_CASES = {json.dumps(test_cases, ensure_ascii=False)};
        
        let currentTestIndex = 0;
        let mediaRecorder = null;
        let audioChunks = [];
        let testResults = [];
        let isRecording = false;
        let recordingStartTime = 0;
        
        async function startTests() {{
            document.getElementById('start-btn').disabled = true;
            document.getElementById('record-btn').disabled = false;
            currentTestIndex = 0;
            testResults = [];
            
            document.getElementById('results-table').style.display = 'none';
            document.getElementById('results-tbody').innerHTML = '';
            
            loadNextTest();
        }}
        
        function loadNextTest() {{
            if (currentTestIndex >= TEST_CASES.length) {{
                completeTests();
                return;
            }}
            
            const test = TEST_CASES[currentTestIndex];
            document.getElementById('status').textContent = `Test ${{currentTestIndex + 1}} of ${{TEST_CASES.length}}`;
            document.getElementById('progress-text').textContent = `Category: ${{test.category}} | ${{test.word_count}} words`;
            document.getElementById('current-text').textContent = test.text;
            document.getElementById('test-info').textContent = test.description;
            document.getElementById('test-display').className = 'active';
            document.getElementById('transcription-result').className = '';
            
            console.log(`Loaded test ${{currentTestIndex + 1}}: ${{test.description}}`);
        }}
        
        async function toggleRecording() {{
            if (!isRecording) {{
                await startRecording();
            }} else {{
                await stopRecording();
            }}
        }}
        
        async function startRecording() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                audioChunks = [];
                
                // Determine best supported audio format (browser compatibility)
                const mimeType = MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' :
                    MediaRecorder.isTypeSupported('audio/mpeg') ? 'audio/mpeg' :
                    'audio/webm';
                
                mediaRecorder = new MediaRecorder(stream, {{ mimeType }});
                mediaRecorder.ondataavailable = (event) => {{
                    audioChunks.push(event.data);
                }};
                
                mediaRecorder.onstop = async () => {{
                    await processRecording();
                }};
                
                recordingStartTime = performance.now();
                mediaRecorder.start();
                isRecording = true;
                
                const recordBtn = document.getElementById('record-btn');
                recordBtn.textContent = '⏹️ Stop Recording';
                recordBtn.className = 'recording';
                
                document.getElementById('status').textContent = '🔴 Recording... Speak clearly';
                
            }} catch (error) {{
                console.error('Failed to start recording:', error);
                alert('Microphone access denied or not available');
            }}
        }}
        
        async function stopRecording() {{
            if (mediaRecorder && isRecording) {{
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                isRecording = false;
                
                const recordBtn = document.getElementById('record-btn');
                recordBtn.textContent = '🎤 Record';
                recordBtn.className = '';
                recordBtn.disabled = true;
                
                document.getElementById('status').textContent = '⏳ Processing...';
            }}
        }}
        
        async function processRecording() {{
            // Get the MIME type that was used for recording
            const mimeType = mediaRecorder.mimeType || 'audio/webm';
            // Determine file extension based on MIME type
            const extension = mimeType.includes('mp4') ? 'mp4' :
                mimeType.includes('mpeg') ? 'mp3' : 'webm';
            
            const audioBlob = new Blob(audioChunks, {{ type: mimeType }});
            const recordingDuration = performance.now() - recordingStartTime;
            
            const test = TEST_CASES[currentTestIndex];
            const result = {{
                test_id: test.id,
                category: test.category,
                original_text: test.text,
                word_count: test.word_count,
                char_count: test.char_count,
                description: test.description,
                recording_duration_ms: Math.round(recordingDuration),
                timestamp: new Date().toISOString()
            }};
            
            try {{
                // Send to API
                const requestStartTime = performance.now();
                
                const formData = new FormData();
                formData.append('audio', audioBlob, `recording.${{extension}}`);
                
                const response = await fetch(`${{API_URL}}/api/transcribe`, {{
                    method: 'POST',
                    body: formData
                }});
                
                const requestDuration = performance.now() - requestStartTime;
                result.network_duration_ms = Math.round(requestDuration);
                
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
                
                const data = await response.json();
                
                if (data.success) {{
                    result.transcription = data.transcript;
                    result.success = true;
                    
                    // Calculate accuracy
                    const accuracy = calculateAccuracy(test.text, data.transcript);
                    result.word_accuracy = accuracy.word_accuracy;
                    result.char_accuracy = accuracy.char_accuracy;
                    result.word_error_rate = accuracy.word_error_rate;
                    
                    // Display results
                    displayTranscriptionResult(data.transcript, accuracy);
                    
                }} else {{
                    result.success = false;
                    result.error = data.error;
                    alert(`Transcription failed: ${{data.error}}`);
                }}
                
            }} catch (error) {{
                console.error('Transcription error:', error);
                result.success = false;
                result.error = error.message;
                alert(`Error: ${{error.message}}`);
            }}
            
            testResults.push(result);
            updateResultsTable(result);
            
            // Wait 2 seconds, then load next test
            setTimeout(() => {{
                currentTestIndex++;
                loadNextTest();
                document.getElementById('record-btn').disabled = false;
            }}, 2000);
        }}
        
        function calculateAccuracy(original, transcription) {{
            // Normalize text
            const normalizeText = (text) => {{
                return text.toLowerCase()
                    .replace(/[.,!?;:]/g, '')
                    .replace(/\\s+/g, ' ')
                    .trim();
            }};
            
            const origNorm = normalizeText(original);
            const transNorm = normalizeText(transcription);
            
            // Word-level comparison
            const origWords = origNorm.split(' ');
            const transWords = transNorm.split(' ');
            
            // Simple word matching (not optimal but good enough)
            const matchedWords = origWords.filter(word => transWords.includes(word)).length;
            const wordAccuracy = (matchedWords / origWords.length) * 100;
            const wordErrorRate = ((origWords.length - matchedWords) / origWords.length) * 100;
            
            // Character-level comparison (Levenshtein would be better but this is simpler)
            const charAccuracy = ((origNorm.length - Math.abs(origNorm.length - transNorm.length)) / origNorm.length) * 100;
            
            return {{
                word_accuracy: wordAccuracy.toFixed(2),
                char_accuracy: charAccuracy.toFixed(2),
                word_error_rate: wordErrorRate.toFixed(2)
            }};
        }}
        
        function displayTranscriptionResult(transcription, accuracy) {{
            document.getElementById('transcription-text').textContent = transcription;
            
            const accDiv = document.getElementById('accuracy-display');
            const wordAcc = parseFloat(accuracy.word_accuracy);
            accDiv.textContent = `Word Accuracy: ${{accuracy.word_accuracy}}% | Char Accuracy: ${{accuracy.char_accuracy}}% | WER: ${{accuracy.word_error_rate}}%`;
            
            if (wordAcc >= 90) {{
                accDiv.className = 'accuracy good';
            }} else if (wordAcc >= 70) {{
                accDiv.className = 'accuracy warning';
            }} else {{
                accDiv.className = 'accuracy poor';
            }}
            
            document.getElementById('transcription-result').className = 'show';
        }}
        
        function updateResultsTable(result) {{
            const tbody = document.getElementById('results-tbody');
            const row = tbody.insertRow();
            row.className = result.success ? 'test-row success' : 'test-row error';
            
            row.insertCell(0).textContent = result.test_id;
            row.insertCell(1).textContent = result.category;
            row.insertCell(2).textContent = result.original_text;
            row.insertCell(3).textContent = result.transcription || 'ERROR';
            row.insertCell(4).textContent = result.success ? `${{result.word_accuracy}}%` : 'N/A';
            row.insertCell(5).textContent = result.network_duration_ms || 'N/A';
            
            document.getElementById('results-table').style.display = 'table';
        }}
        
        function completeTests() {{
            document.getElementById('status').textContent = '✅ All tests completed!';
            document.getElementById('test-display').className = '';
            document.getElementById('current-text').textContent = '';
            document.getElementById('test-info').textContent = 'Testing complete. Download results below.';
            document.getElementById('download-btn').disabled = false;
            
            displayStats();
            
            // Auto-download
            downloadResults();
        }}
        
        function displayStats() {{
            const successfulTests = testResults.filter(r => r.success);
            const avgWordAcc = successfulTests.reduce((sum, r) => sum + parseFloat(r.word_accuracy), 0) / successfulTests.length;
            const avgCharAcc = successfulTests.reduce((sum, r) => sum + parseFloat(r.char_accuracy), 0) / successfulTests.length;
            const avgWER = successfulTests.reduce((sum, r) => sum + parseFloat(r.word_error_rate), 0) / successfulTests.length;
            const avgTime = successfulTests.reduce((sum, r) => sum + r.network_duration_ms, 0) / successfulTests.length;
            
            const statsHTML = `
                <div class="metric">
                    <div class="metric-value">${{testResults.length}}</div>
                    <div class="metric-label">Total Tests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{successfulTests.length}}</div>
                    <div class="metric-label">Successful</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{avgWordAcc.toFixed(1)}}%</div>
                    <div class="metric-label">Avg Word Accuracy</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{avgCharAcc.toFixed(1)}}%</div>
                    <div class="metric-label">Avg Char Accuracy</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{avgWER.toFixed(1)}}%</div>
                    <div class="metric-label">Avg WER</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${{avgTime.toFixed(0)}}ms</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
            `;
            
            document.getElementById('stats-content').innerHTML = statsHTML;
            document.getElementById('stats').className = 'show';
        }}
        
        function downloadResults() {{
            const resultsData = {{
                metadata: {{
                    test_date: new Date().toISOString(),
                    api_url: API_URL,
                    total_tests: testResults.length,
                    successful_tests: testResults.filter(r => r.success).length
                }},
                results: testResults
            }};
            
            const blob = new Blob([JSON.stringify(resultsData, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `stt_results_${{Date.now()}}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
"""
    
    # Write HTML file
    with open(test_harness_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"STT test harness created: {test_harness_path}")
    print(f"Results will be saved to: {results_path}")
    
    return test_harness_path


def main():
    parser = argparse.ArgumentParser(description='Test Voice Input (Speech-to-Text) Performance')
    parser.add_argument('--api-url', default='https://my-orama.my-domain.com',
                       help='Base API URL')
    
    args = parser.parse_args()
    
    # Load test cases
    test_cases, metadata = load_test_cases()
    
    # Print summary
    summary = get_test_suite_summary(test_cases)
    
    print("=" * 70)
    print("VOICE INPUT (SPEECH-TO-TEXT) PERFORMANCE TEST SUITE")
    print("=" * 70)
    print(f"Total test cases: {summary['total_tests']}")
    print(f"Total words: {summary['total_words']}")
    print(f"Total characters: {summary['total_chars']}")
    print(f"Average words per test: {summary['avg_words']:.1f}")
    print(f"Average characters per test: {summary['avg_chars']:.1f}")
    print()
    print("Test Distribution by Category:")
    for cat, stats in sorted(summary['categories'].items()):
        print(f"  • {cat.capitalize()}: {stats['count']} tests (avg {stats['avg_words']:.0f} words)")
    print("=" * 70)
    print()
    
    # Generate test harness
    print("=" * 70)
    print("VOICE INPUT TESTING SETUP")
    print("=" * 70)
    print(f"API URL: {args.api_url}")
    print(f"Total test cases: {len(test_cases)}")
    print("=" * 70)
    print()
    
    harness_path = generate_test_harness(args.api_url, test_cases)
    
    print()
    print("TESTING INSTRUCTIONS:")
    print("=" * 70)
    print("1. Open the test harness in your browser:")
    print(f"   file://{harness_path.absolute()}")
    print()
    print("2. Allow microphone access when prompted")
    print()
    print("3. For EACH test:")
    print("   a. Read the displayed Greek text OUT LOUD")
    print("   b. Click 'Record' button")
    print("   c. Speak clearly into your microphone")
    print("   d. Click 'Stop Recording'")
    print("   e. Wait for transcription result")
    print("   f. Review accuracy before next test")
    print()
    print("4. After all 20 tests, results will auto-download")
    print()
    print("5. Move the downloaded JSON file to:")
    print(f"   {Path(__file__).parent / 'results'}/")
    print()
    print("6. Run analysis:")
    print("   python analyze_results.py results/stt_results_*.json")
    print("=" * 70)
    print()
    print("Press ENTER when tests are complete...")
    input()
    
    print("Speech-to-text testing complete!")


if __name__ == "__main__":
    main()
