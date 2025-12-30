const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testVoiceAgentDebugUI() {
    const browser = await chromium.launch({ 
        headless: false,
        args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
    });
    const context = await browser.newContext({
        permissions: ['microphone']
    });
    const page = await context.newPage();

    const screenshotDir = path.join(__dirname, 'test_screenshots');
    if (!fs.existsSync(screenshotDir)) {
        fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const testResults = {
        timestamp: new Date().toISOString(),
        steps: [],
        ledStates: {},
        stateValues: {},
        eventLog: [],
        failurePoint: null,
        success: false
    };

    function logStep(step, status, details) {
        const entry = { step, status, details, timestamp: new Date().toISOString() };
        testResults.steps.push(entry);
        console.log('[' + status + '] ' + step + ': ' + details);
    }

    try {
        console.log('=== AGENT_66 CONNECTION FLOW TEST ===\n');

        logStep('Navigate', 'START', 'Loading debug page');
        await page.goto('http://localhost:9000/voice-agent-selector-debug.html', { 
            waitUntil: 'networkidle',
            timeout: 30000
        });
        logStep('Navigate', 'SUCCESS', 'Page loaded');

        await page.screenshot({ path: path.join(screenshotDir, '01_initial_page.png'), fullPage: true });
        console.log('Screenshot: 01_initial_page.png');

        logStep('Initialize', 'START', 'Waiting for page initialization');
        await page.waitForTimeout(2000);
        
        const initialLedStates = await page.evaluate(() => {
            return {
                webSocket: document.getElementById('ledWebSocket').getAttribute('data-state'),
                liveKit: document.getElementById('ledLiveKit').getAttribute('data-state'),
                agentSelection: document.getElementById('ledAgentSelection').getAttribute('data-state'),
                audioInput: document.getElementById('ledAudioInput').getAttribute('data-state'),
                audioOutput: document.getElementById('ledAudioOutput').getAttribute('data-state'),
                messageSend: document.getElementById('ledMessageSend').getAttribute('data-state'),
                messageReceive: document.getElementById('ledMessageReceive').getAttribute('data-state'),
                agentResponse: document.getElementById('ledAgentResponse').getAttribute('data-state')
            };
        });
        testResults.ledStates.initial = initialLedStates;
        logStep('Initialize', 'SUCCESS', 'LED states captured');

        const initialStates = await page.evaluate(() => {
            return {
                agentId: document.getElementById('stateAgentId').textContent,
                agentName: document.getElementById('stateAgentName').textContent,
                roomName: document.getElementById('stateRoomName').textContent,
                webSocketUrl: document.getElementById('stateWebSocketUrl').textContent,
                liveKitState: document.getElementById('stateLiveKitState').textContent,
                audioState: document.getElementById('stateAudioState').textContent,
                participantCount: document.getElementById('stateParticipantCount').textContent,
                errorMessage: document.getElementById('stateErrorMessage').textContent
            };
        });
        testResults.stateValues.initial = initialStates;
        logStep('Initialize', 'SUCCESS', 'State values captured');

        logStep('Agent Selection', 'START', 'Checking Agent_66 selection');
        const agentName = await page.locator('#stateAgentName').textContent();
        if (agentName.includes('Agent_66')) {
            logStep('Agent Selection', 'SUCCESS', 'Agent_66 auto-selected: ' + agentName);
        } else {
            logStep('Agent Selection', 'WARNING', 'Expected Agent_66, got: ' + agentName);
        }
        await page.screenshot({ path: path.join(screenshotDir, '02_agent_selected.png'), fullPage: true });

        logStep('Connect Button', 'START', 'Clicking Connect button');
        const connectBtn = page.locator('#connectBtn');
        await connectBtn.click();
        logStep('Connect Button', 'SUCCESS', 'Connect button clicked');
        await page.screenshot({ path: path.join(screenshotDir, '03_connecting.png'), fullPage: true });

        logStep('Connection Flow', 'START', 'Monitoring LED state changes');
        
        for (let i = 0; i < 10; i++) {
            await page.waitForTimeout(2000);
            
            const currentLeds = await page.evaluate(() => {
                return {
                    webSocket: document.getElementById('ledWebSocket').getAttribute('data-state'),
                    liveKit: document.getElementById('ledLiveKit').getAttribute('data-state'),
                    agentSelection: document.getElementById('ledAgentSelection').getAttribute('data-state'),
                    audioInput: document.getElementById('ledAudioInput').getAttribute('data-state'),
                    audioOutput: document.getElementById('ledAudioOutput').getAttribute('data-state'),
                    messageSend: document.getElementById('ledMessageSend').getAttribute('data-state'),
                    messageReceive: document.getElementById('ledMessageReceive').getAttribute('data-state'),
                    agentResponse: document.getElementById('ledAgentResponse').getAttribute('data-state')
                };
            });
            
            const currentStates = await page.evaluate(() => {
                return {
                    liveKitState: document.getElementById('stateLiveKitState').textContent,
                    participantCount: document.getElementById('stateParticipantCount').textContent,
                    audioState: document.getElementById('stateAudioState').textContent,
                    errorMessage: document.getElementById('stateErrorMessage').textContent
                };
            });
            
            const timeKey = 't' + (i*2) + 's';
            testResults.ledStates[timeKey] = currentLeds;
            testResults.stateValues[timeKey] = currentStates;
            
            console.log('\n--- Time: ' + (i*2) + 's ---');
            console.log('LEDs:', currentLeds);
            console.log('States:', currentStates);
            
            if (i === 2 || i === 5 || i === 9) {
                await page.screenshot({ 
                    path: path.join(screenshotDir, '04_connection_' + (i*2) + 's.png'), 
                    fullPage: true 
                });
            }
            
            if (currentLeds.agentResponse === 'connected') {
                logStep('Connection Flow', 'SUCCESS', 'Agent connected at ' + (i*2) + 's');
                testResults.success = true;
                break;
            }
            
            if (currentLeds.liveKit === 'error' || currentLeds.audioInput === 'error') {
                logStep('Connection Flow', 'ERROR', 'Error state detected at ' + (i*2) + 's');
                testResults.failurePoint = 'Error at ' + (i*2) + 's';
                break;
            }
        }

        await page.waitForTimeout(2000);
        const finalLeds = await page.evaluate(() => {
            return {
                webSocket: document.getElementById('ledWebSocket').getAttribute('data-state'),
                liveKit: document.getElementById('ledLiveKit').getAttribute('data-state'),
                agentSelection: document.getElementById('ledAgentSelection').getAttribute('data-state'),
                audioInput: document.getElementById('ledAudioInput').getAttribute('data-state'),
                audioOutput: document.getElementById('ledAudioOutput').getAttribute('data-state'),
                messageSend: document.getElementById('ledMessageSend').getAttribute('data-state'),
                messageReceive: document.getElementById('ledMessageReceive').getAttribute('data-state'),
                agentResponse: document.getElementById('ledAgentResponse').getAttribute('data-state')
            };
        });
        
        const finalStates = await page.evaluate(() => {
            return {
                agentId: document.getElementById('stateAgentId').textContent,
                agentName: document.getElementById('stateAgentName').textContent,
                roomName: document.getElementById('stateRoomName').textContent,
                liveKitState: document.getElementById('stateLiveKitState').textContent,
                participantCount: document.getElementById('stateParticipantCount').textContent,
                audioState: document.getElementById('stateAudioState').textContent,
                errorMessage: document.getElementById('stateErrorMessage').textContent
            };
        });
        
        testResults.ledStates.final = finalLeds;
        testResults.stateValues.final = finalStates;

        const eventLog = await page.evaluate(() => {
            const entries = Array.from(document.querySelectorAll('.event-log-entry'));
            return entries.map(entry => ({
                timestamp: entry.getAttribute('data-timestamp'),
                category: entry.getAttribute('data-category'),
                text: entry.textContent
            }));
        });
        testResults.eventLog = eventLog;
        
        console.log('\n=== EVENT LOG ===');
        eventLog.forEach(entry => {
            console.log('[' + entry.category + '] ' + entry.text);
        });

        await page.screenshot({ path: path.join(screenshotDir, '05_final_state.png'), fullPage: true });

        console.log('\n=== DIAGNOSTIC ANALYSIS ===');
        console.log('Final LED States:');
        Object.entries(finalLeds).forEach(([led, state]) => {
            const symbol = state === 'connected' ? '✓' : state === 'error' ? '✗' : state === 'connecting' ? '⋯' : '○';
            console.log('  ' + symbol + ' ' + led + ': ' + state);
        });
        
        console.log('\nFinal State Values:');
        Object.entries(finalStates).forEach(([key, value]) => {
            console.log('  ' + key + ': ' + value);
        });

        if (!testResults.success) {
            if (finalLeds.webSocket !== 'connected') {
                testResults.failurePoint = 'WebSocket connection failed';
            } else if (finalLeds.liveKit !== 'connected') {
                testResults.failurePoint = 'LiveKit room connection failed';
            } else if (finalLeds.audioInput !== 'connected') {
                testResults.failurePoint = 'Audio input (microphone) failed';
            } else if (finalLeds.agentResponse !== 'connected') {
                testResults.failurePoint = 'Agent failed to join room';
            } else {
                testResults.failurePoint = 'Unknown - LEDs show connected but no agent response';
            }
        }

        console.log('\nFailure Point: ' + (testResults.failurePoint || 'None - Success!'));
        console.log('Participant Count: ' + finalStates.participantCount);
        console.log('Error Message: ' + finalStates.errorMessage);

        const resultsPath = path.join(__dirname, 'test_results.json');
        fs.writeFileSync(resultsPath, JSON.stringify(testResults, null, 2));
        console.log('\nTest results saved to: ' + resultsPath);

    } catch (error) {
        console.error('Test failed with error:', error);
        testResults.failurePoint = 'Exception: ' + error.message;
        await page.screenshot({ path: path.join(screenshotDir, '99_error.png'), fullPage: true });
    } finally {
        console.log('\n=== TEST COMPLETE ===');
        console.log('Screenshots saved to:', screenshotDir);
        
        console.log('\nBrowser window left open for manual inspection.');
        console.log('Close the browser manually when done.');
        
        await new Promise(() => {});
    }
}

testVoiceAgentDebugUI();
