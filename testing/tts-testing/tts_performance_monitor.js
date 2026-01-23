/**
 * TTS Auto-Speak Performance Monitor (Client-Side)
 * =================================================
 * 
 * This script monitors and measures client-side TTS performance metrics:
 * 1. Request initiation time
 * 2. Network transfer time
 * 3. Audio blob creation time
 * 4. Audio decoding/compilation time
 * 5. Audio playback start time
 * 6. Audio duration
 * 7. Total time-to-first-audio
 * 
 * Usage:
 *   const monitor = new TTSPerformanceMonitor(apiBaseUrl);
 *   const result = await monitor.testTTS(testCase);
 */

class TTSPerformanceMonitor {
    constructor(apiBaseUrl, useMonitoredEndpoint = false) {
        this.apiBaseUrl = apiBaseUrl;
        this.endpoint = useMonitoredEndpoint ? '/api/speak/monitored' : '/api/speak';
        this.results = [];
    }

    /**
     * Test TTS performance for a single test case.
     * 
     * @param {Object} testCase - Test case object with id, text, category, etc.
     * @returns {Promise<Object>} - Performance metrics
     */
    async testTTS(testCase) {
        const metrics = {
            test_id: testCase.id,
            category: testCase.category,
            text_length_chars: testCase.char_count,
            text_length_words: testCase.word_count,
            description: testCase.description,
            timestamp: new Date().toISOString(),
            success: false
        };

        try {
            // 1. Request initiation
            const requestStartTime = performance.now();
            metrics.request_start_time = requestStartTime;

            // 2. Send request and measure network time
            const response = await fetch(`${this.apiBaseUrl}${this.endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: testCase.text,
                    test_id: testCase.id
                })
            });

            const responseReceivedTime = performance.now();
            metrics.network_request_duration_ms = responseReceivedTime - requestStartTime;

            // Check response status
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Extract server-side timing from headers (if available)
            metrics.server_time_ms = parseFloat(response.headers.get('X-Server-Time-Ms')) || null;
            metrics.api_time_ms = parseFloat(response.headers.get('X-API-Time-Ms')) || null;
            metrics.audio_size_bytes = parseInt(response.headers.get('X-Audio-Size-Bytes')) || null;

            // 3. Convert response to blob and measure time
            const blobStartTime = performance.now();
            const blob = await response.blob();
            const blobCreatedTime = performance.now();
            
            metrics.blob_creation_duration_ms = blobCreatedTime - blobStartTime;
            metrics.blob_size_bytes = blob.size;
            metrics.blob_size_kb = (blob.size / 1024).toFixed(2);

            // 4. Create object URL
            const urlCreationStartTime = performance.now();
            const audioUrl = URL.createObjectURL(blob);
            const urlCreatedTime = performance.now();
            
            metrics.url_creation_duration_ms = urlCreatedTime - urlCreationStartTime;

            // 5. Create and load audio element
            const audioLoadStartTime = performance.now();
            const audio = new Audio(audioUrl);

            // Wait for audio to be ready to play (canplaythrough event)
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Audio load timeout'));
                }, 10000); // 10 second timeout

                audio.addEventListener('canplaythrough', () => {
                    clearTimeout(timeout);
                    resolve();
                }, { once: true });

                audio.addEventListener('error', (e) => {
                    clearTimeout(timeout);
                    reject(new Error(`Audio load error: ${e.message}`));
                });

                // Start loading
                audio.load();
            });

            const audioReadyTime = performance.now();
            metrics.audio_decoding_duration_ms = audioReadyTime - audioLoadStartTime;
            metrics.audio_duration_seconds = audio.duration;

            // 6. Play audio and measure playback start
            const playbackStartTime = performance.now();
            
            await audio.play();
            
            const playbackStartedTime = performance.now();
            metrics.playback_start_latency_ms = playbackStartedTime - playbackStartTime;

            // 7. Wait for audio to finish (optional - can be skipped for faster testing)
            const playbackFinishPromise = new Promise((resolve) => {
                audio.addEventListener('ended', () => {
                    const playbackEndTime = performance.now();
                    metrics.total_playback_duration_ms = playbackEndTime - playbackStartedTime;
                    resolve();
                }, { once: true });
            });

            // Calculate total time from request to first audio
            metrics.total_time_to_audio_ms = playbackStartedTime - requestStartTime;

            // Calculate breakdown percentages
            const totalTime = metrics.total_time_to_audio_ms;
            metrics.network_percentage = ((metrics.network_request_duration_ms / totalTime) * 100).toFixed(1);
            metrics.blob_percentage = ((metrics.blob_creation_duration_ms / totalTime) * 100).toFixed(1);
            metrics.decoding_percentage = ((metrics.audio_decoding_duration_ms / totalTime) * 100).toFixed(1);
            metrics.playback_percentage = ((metrics.playback_start_latency_ms / totalTime) * 100).toFixed(1);

            // Calculate throughput metrics
            if (metrics.blob_size_bytes && metrics.network_request_duration_ms) {
                metrics.download_speed_kbps = ((metrics.blob_size_bytes * 8) / metrics.network_request_duration_ms).toFixed(2);
            }

            // Character-to-audio ratio
            if (metrics.audio_duration_seconds) {
                metrics.chars_per_second_of_audio = (testCase.char_count / metrics.audio_duration_seconds).toFixed(2);
            }

            // Wait for playback to finish (optional)
            // await playbackFinishPromise;

            // Clean up
            audio.pause();
            audio.src = '';
            URL.revokeObjectURL(audioUrl);

            metrics.success = true;

        } catch (error) {
            metrics.success = false;
            metrics.error = error.message;
            metrics.error_stack = error.stack;
        }

        // Store result
        this.results.push(metrics);
        
        return metrics;
    }

    /**
     * Run tests for multiple test cases with delay between tests.
     * 
     * @param {Array} testCases - Array of test case objects
     * @param {number} delayMs - Delay between tests in milliseconds
     * @param {Function} progressCallback - Called after each test with (current, total, result)
     * @returns {Promise<Array>} - Array of all test results
     */
    async runTestSuite(testCases, delayMs = 1000, progressCallback = null) {
        const results = [];
        
        for (let i = 0; i < testCases.length; i++) {
            const testCase = testCases[i];
            
            console.log(`[${i + 1}/${testCases.length}] Testing: ${testCase.description}`);
            
            const result = await this.testTTS(testCase);
            results.push(result);
            
            if (progressCallback) {
                progressCallback(i + 1, testCases.length, result);
            }
            
            // Delay before next test (except for last test)
            if (i < testCases.length - 1 && delayMs > 0) {
                await new Promise(resolve => setTimeout(resolve, delayMs));
            }
        }
        
        return results;
    }

    /**
     * Export results as JSON.
     * 
     * @returns {string} - JSON string of all results
     */
    exportResultsJSON() {
        return JSON.stringify(this.results, null, 2);
    }

    /**
     * Export results as JSON Lines (one JSON object per line).
     * 
     * @returns {string} - JSONL string
     */
    exportResultsJSONL() {
        return this.results.map(r => JSON.stringify(r)).join('\n');
    }

    /**
     * Download results as a file.
     * 
     * @param {string} filename - Name of the file to download
     * @param {string} format - 'json' or 'jsonl'
     */
    downloadResults(filename = 'tts_client_results.json', format = 'json') {
        const content = format === 'jsonl' ? this.exportResultsJSONL() : this.exportResultsJSON();
        const blob = new Blob([content], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Get summary statistics of test results.
     * 
     * @returns {Object} - Summary statistics
     */
    getSummaryStats() {
        const successfulTests = this.results.filter(r => r.success);
        
        if (successfulTests.length === 0) {
            return { error: 'No successful tests' };
        }

        const stats = {
            total_tests: this.results.length,
            successful_tests: successfulTests.length,
            failed_tests: this.results.length - successfulTests.length,
            success_rate: ((successfulTests.length / this.results.length) * 100).toFixed(1)
        };

        // Calculate averages
        const metrics = ['total_time_to_audio_ms', 'network_request_duration_ms', 
                        'blob_creation_duration_ms', 'audio_decoding_duration_ms',
                        'audio_duration_seconds', 'blob_size_kb'];

        metrics.forEach(metric => {
            const values = successfulTests
                .map(r => r[metric])
                .filter(v => v !== null && v !== undefined);
            
            if (values.length > 0) {
                const sum = values.reduce((a, b) => a + b, 0);
                const mean = sum / values.length;
                const sorted = values.sort((a, b) => a - b);
                const median = sorted[Math.floor(sorted.length / 2)];
                const min = Math.min(...values);
                const max = Math.max(...values);
                
                stats[metric] = {
                    mean: parseFloat(mean.toFixed(2)),
                    median: parseFloat(median.toFixed(2)),
                    min: parseFloat(min.toFixed(2)),
                    max: parseFloat(max.toFixed(2))
                };
            }
        });

        return stats;
    }

    /**
     * Print summary to console.
     */
    printSummary() {
        const stats = this.getSummaryStats();
        console.log('\n=== TTS Performance Test Summary ===');
        console.log(`Total Tests: ${stats.total_tests}`);
        console.log(`Successful: ${stats.successful_tests} (${stats.success_rate}%)`);
        console.log(`Failed: ${stats.failed_tests}`);
        console.log('\nTiming Metrics (in ms):');
        console.log(`  Total Time to Audio: ${stats.total_time_to_audio_ms?.mean} ms (median: ${stats.total_time_to_audio_ms?.median})`);
        console.log(`  Network Request: ${stats.network_request_duration_ms?.mean} ms`);
        console.log(`  Blob Creation: ${stats.blob_creation_duration_ms?.mean} ms`);
        console.log(`  Audio Decoding: ${stats.audio_decoding_duration_ms?.mean} ms`);
        console.log(`\nAudio Metrics:`);
        console.log(`  Average Duration: ${stats.audio_duration_seconds?.mean} seconds`);
        console.log(`  Average Size: ${stats.blob_size_kb?.mean} KB`);
        console.log('=====================================\n');
    }
}

// Export for use in Node.js or browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TTSPerformanceMonitor;
}
