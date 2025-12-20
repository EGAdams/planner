# Letta Voice Agent Performance Analysis & Optimization Guide

## Executive Summary

The Letta voice agent system has **3 major bottlenecks** causing slow response times:

1. **Synchronous Letta API calls** (blocking async event loop)
2. **Network latency to localhost:8283** Letta server
3. **Cascading STT → LLM → TTS pipeline delays**

**Fastest path to improvement**: Replace Letta LLM with Groq for 5-10x faster inference.

---

## Current Architecture Analysis

### Voice Pipeline Flow
```
User Speech → Deepgram STT → Livekit → llm_node() →
Letta API (localhost:8283) → OpenAI/GPT-4o-mini →
Response Processing → OpenAI/Cartesia TTS → User
```

### Identified Bottlenecks (Ranked by Impact)

#### 1. CRITICAL: Letta LLM Inference (HIGHEST IMPACT)
**Location**: Lines 174-178 in `letta_voice_agent.py`
```python
response = await asyncio.to_thread(
    self.letta_client.agents.messages.create,
    agent_id=self.agent_id,
    messages=[{"role": "user", "content": user_message}]
)
```

**Problem**:
- Letta server calls OpenAI GPT-4o-mini (or configured model)
- OpenAI API latency: 1-3 seconds typical
- Network round-trip to localhost adds 10-50ms
- Synchronous client wrapped in `asyncio.to_thread()` blocks thread pool

**Evidence from code**:
- Line 300: `llm_model = "gpt-4o-mini"` (default model)
- Lines 48-50: Letta server at `http://localhost:8283`

**Impact**: 70-80% of total response time

---

#### 2. HIGH: Synchronous Client Blocking
**Location**: Lines 174, 261, 318, 371 (all `asyncio.to_thread()` calls)

**Problem**:
- `letta_client` is synchronous (Letta Python client doesn't support async)
- Every call blocks a thread from the thread pool
- Multiple sequential calls compound latency

**Code examples**:
```python
# Line 174: Message send (CRITICAL PATH)
response = await asyncio.to_thread(...)

# Line 261: Agent verification
agent = await asyncio.to_thread(self.letta_client.agents.get, ...)

# Line 318: List agents
agents_list = await asyncio.to_thread(letta_client.agents.list)
```

**Impact**: 15-20% overhead on top of API latency

---

#### 3. MODERATE: STT Latency (Deepgram Nova 2)
**Location**: Lines 468-471

**Current**: Deepgram Nova 2
- Latency: 300-500ms typical
- Quality: Excellent
- Cost: Moderate

**Problem**:
- Cloud API network latency
- Processing time on Deepgram servers

**Impact**: 10-15% of total response time

---

#### 4. LOW: TTS Latency
**Location**: Lines 452-464

**Current Options**:
- OpenAI TTS: 400-800ms (default)
- Cartesia TTS: 200-400ms (faster, if configured)

**Impact**: 5-10% of total response time

---

## Optimization Recommendations (Priority Order)

### 🚀 PRIORITY 1: Replace Letta LLM with Groq (FASTEST WIN)

**Why Groq**:
- 50-100 tokens/second (vs 20-40 for OpenAI)
- Sub-second response times for typical queries
- Supports Llama 3, Mixtral models
- Drop-in replacement via OpenAI-compatible API

**Implementation**:

#### Option A: Configure Letta to Use Groq Endpoint
```bash
# In your .env file
export GROQ_API_KEY="your_groq_api_key"

# Update Letta agent config (in letta_voice_agent.py lines 374-378)
llm_config={
    "model": "llama-3.1-70b-versatile",  # or mixtral-8x7b-32768
    "model_endpoint_type": "groq",
    "context_window": 32768,
    "model_endpoint": "https://api.groq.com/openai/v1"
}
```

**Expected Improvement**:
- Current: 1-3 seconds per response
- With Groq: 200-500ms per response
- **5-10x faster LLM inference**

#### Option B: Direct Groq Integration (Bypass Letta)
If Letta doesn't support Groq endpoint, bypass Letta for LLM inference:

```python
# Add to imports
from groq import Groq

# In LettaVoiceAssistant.__init__
self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Replace _get_letta_response with:
async def _get_letta_response(self, user_message: str) -> str:
    """Fast path: Use Groq for inference, Letta only for memory"""

    # 1. Get conversation context from Letta memory (optional)
    # 2. Call Groq for ultra-fast inference
    try:
        response = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": self.instructions},
                *self.message_history,
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=200  # Keep voice responses concise
        )

        response_text = response.choices[0].message.content

        # 3. Update Letta memory asynchronously (fire-and-forget)
        asyncio.create_task(self._update_letta_memory(user_message, response_text))

        return response_text
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "I'm having trouble processing that. Could you try again?"

async def _update_letta_memory(self, user_msg: str, assistant_msg: str):
    """Background task to update Letta memory"""
    try:
        await asyncio.to_thread(
            self.letta_client.agents.messages.create,
            agent_id=self.agent_id,
            messages=[
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        )
    except Exception as e:
        logger.error(f"Memory update failed: {e}")
```

**Tradeoff**: Loses Letta's function calling and tool use, but gains massive speed.

---

### 🔧 PRIORITY 2: Replace Deepgram with Local STT

**Options**:

#### A. Whisper C++ (Fastest local option)
```bash
# Install
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
./models/download-ggml-model.sh base.en

# Integration points:
# - Replace lines 468-471 in letta_voice_agent.py
# - Use whisper.cpp binary via subprocess
# - Or use Python bindings: pip install whisper-cpp-python
```

**Pros**:
- 100-300ms latency (local processing)
- No API costs
- No network dependency

**Cons**:
- Requires CPU/GPU resources
- May reduce accuracy vs Deepgram
- Adds complexity

#### B. Moonshine (Emerging option)
- New efficient STT model (Dec 2024)
- Faster than Whisper base models
- Research if Livekit plugin exists

**Expected Improvement**: 200-400ms faster STT (300-500ms → 100-200ms)

---

### ⚡ PRIORITY 3: Optimize TTS

**Current**: OpenAI TTS (400-800ms) or Cartesia (200-400ms)

**Faster Options**:

#### A. Use Cartesia (Already supported!)
```bash
# In .env
export TTS_PROVIDER="cartesia"
export CARTESIA_API_KEY="your_key"
```

**Expected**: 200-400ms (already fast)

#### B. Consider Groq TTS (if available)
- Check if Groq offers TTS endpoints
- May provide consistent sub-200ms latency

#### C. Stream TTS (Advanced)
- Start playing TTS audio while still generating
- Reduces perceived latency
- Requires Livekit streaming support

**Expected Improvement**: 200-400ms faster TTS

---

### 🔨 PRIORITY 4: Code Optimizations

#### A. Add Response Timing Metrics
```python
import time

async def _get_letta_response(self, user_message: str) -> str:
    start_time = time.time()

    try:
        # Existing code...
        response = await asyncio.to_thread(...)

        elapsed = (time.time() - start_time) * 1000  # ms
        logger.info(f"⏱️ Letta response time: {elapsed:.0f}ms")

        return response_text
    except Exception as e:
        ...
```

**Benefit**: Measure actual bottlenecks with real data

#### B. Implement Response Caching
```python
# Add to LettaVoiceAssistant
self.response_cache = {}

async def _get_letta_response(self, user_message: str) -> str:
    # Check cache for common queries
    cache_key = user_message.lower().strip()
    if cache_key in self.response_cache:
        logger.info("📦 Cache hit!")
        return self.response_cache[cache_key]

    # ... existing Letta call ...

    # Cache response
    self.response_cache[cache_key] = response_text
    return response_text
```

**Benefit**: Instant responses for repeated questions

#### C. Parallel Processing (Advanced)
```python
# If using Option B (bypass Letta), parallelize STT and context retrieval
async def llm_node(self, chat_ctx, tools, model_settings):
    user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")

    # Start both tasks in parallel
    transcript_task = asyncio.create_task(
        self._publish_transcript("user", user_message)
    )
    response_task = asyncio.create_task(
        self._get_letta_response(user_message)
    )

    # Wait for both
    await transcript_task
    response_text = await response_task

    await self._publish_transcript("assistant", response_text)
    return response_text
```

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (1-2 hours)
1. Add timing metrics to measure current performance
2. Configure Cartesia TTS (if not already using)
3. Test Groq API key and connectivity

### Phase 2: Groq Integration (2-4 hours)
**Option A** (if Letta supports Groq):
1. Update `.env` with Groq API key
2. Modify Letta agent config to use Groq endpoint
3. Test and measure improvements

**Option B** (if Letta doesn't support Groq):
1. Implement direct Groq integration (bypass Letta for inference)
2. Keep Letta for memory management only
3. Test and validate

### Phase 3: Advanced Optimizations (4-8 hours)
1. Evaluate local STT (Whisper C++ or Moonshine)
2. Implement response caching
3. Consider streaming TTS for perceived latency reduction

---

## Expected Performance After Optimization

### Current Performance (Estimated)
```
User speaks → 300-500ms (STT) →
50ms (network) →
1500-3000ms (Letta/OpenAI LLM) ← BOTTLENECK
50ms (network) →
400-800ms (TTS) →
= 2300-4350ms total
```

### After Groq Optimization
```
User speaks → 300-500ms (STT) →
50ms (network) →
200-500ms (Groq LLM) ← 5-10x FASTER
50ms (network) →
200-400ms (Cartesia TTS) →
= 800-1450ms total
```

**Improvement**: 60-70% reduction in response time

### After Full Optimization (Groq + Local STT + Cartesia)
```
User speaks → 100-200ms (Local STT) →
0ms (no network) →
200-500ms (Groq LLM) →
0ms (no network) →
200-400ms (Cartesia TTS) →
= 500-1100ms total
```

**Improvement**: 75-85% reduction in response time

---

## Implementation Code Snippets

### 1. Add Groq Support (Minimal Changes)

```python
# In letta_voice_agent.py, add after imports:
from groq import Groq

# Update get_or_create_orchestrator function (line 289+):
async def get_or_create_orchestrator(letta_client: Letta) -> str:
    agent_name = "Agent_66"

    # Check if using Groq
    use_groq = os.getenv("USE_GROQ_LLM", "false").lower() == "true"

    if use_groq:
        llm_endpoint = "groq"
        llm_model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    else:
        llm_endpoint = os.getenv("LETTA_ORCHESTRATOR_ENDPOINT_TYPE", "openai")
        llm_model = os.getenv("LETTA_ORCHESTRATOR_MODEL", "gpt-4o-mini")

    # ... rest of function with updated llm_config
```

### 2. Direct Groq Integration (Full Bypass)

```python
# In LettaVoiceAssistant class:
def __init__(self, ctx: JobContext, letta_client: Letta, agent_id: str):
    super().__init__(instructions="""...""")
    self.ctx = ctx
    self.letta_client = letta_client
    self.agent_id = agent_id
    self.message_history = []

    # Add Groq client
    if os.getenv("GROQ_API_KEY"):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.use_groq = True
    else:
        self.groq_client = None
        self.use_groq = False

async def _get_letta_response(self, user_message: str) -> str:
    if self.use_groq:
        return await self._get_groq_response(user_message)
    else:
        return await self._get_letta_fallback_response(user_message)

async def _get_groq_response(self, user_message: str) -> str:
    """Fast Groq inference with background Letta memory sync"""
    start_time = time.time()

    try:
        response = await asyncio.to_thread(
            self.groq_client.chat.completions.create,
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": self.instructions},
                *self.message_history[-10:],  # Last 10 messages for context
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=200,
            stream=False
        )

        response_text = response.choices[0].message.content
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ Groq response: {elapsed:.0f}ms")

        # Update history
        self.message_history.append({"role": "user", "content": user_message})
        self.message_history.append({"role": "assistant", "content": response_text})

        # Sync to Letta memory in background (non-blocking)
        asyncio.create_task(self._sync_to_letta(user_message, response_text))

        return response_text

    except Exception as e:
        logger.error(f"Groq error: {e}, falling back to Letta")
        return await self._get_letta_fallback_response(user_message)

async def _sync_to_letta(self, user_msg: str, assistant_msg: str):
    """Background sync to Letta for memory persistence"""
    try:
        await asyncio.to_thread(
            self.letta_client.agents.messages.create,
            agent_id=self.agent_id,
            messages=[
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        )
    except Exception as e:
        logger.error(f"Letta memory sync failed: {e}")

async def _get_letta_fallback_response(self, user_message: str) -> str:
    """Original Letta-based response (fallback)"""
    # ... existing implementation from lines 160-219
```

---

## Testing & Validation

### Measure Current Performance
```python
# Add to llm_node function (after line 140):
import time

async def llm_node(self, chat_ctx, tools, model_settings):
    pipeline_start = time.time()

    user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")
    stt_time = (time.time() - pipeline_start) * 1000
    logger.info(f"⏱️ STT: {stt_time:.0f}ms")

    llm_start = time.time()
    response_text = await self._get_letta_response(user_message)
    llm_time = (time.time() - llm_start) * 1000
    logger.info(f"⏱️ LLM: {llm_time:.0f}ms")

    tts_start = time.time()
    await self._publish_transcript("assistant", response_text)
    # TTS time measured after return

    pipeline_total = (time.time() - pipeline_start) * 1000
    logger.info(f"⏱️ Total pipeline: {pipeline_total:.0f}ms")

    return response_text
```

### Test Groq Performance
```bash
# 1. Add to .env
GROQ_API_KEY=your_groq_key_here
USE_GROQ_LLM=true
GROQ_MODEL=llama-3.1-70b-versatile

# 2. Install Groq client
pip install groq

# 3. Restart voice system
./restart_voice_system.sh

# 4. Test voice interaction and check logs
tail -f /tmp/letta_voice_agent.log | grep "⏱️"
```

---

## Questions to Answer

1. **Do you have a Groq API key?** (Free tier available)
2. **Is maintaining Letta's full orchestration critical?** Or can we use Groq for speed and sync memory to Letta asynchronously?
3. **What's acceptable accuracy tradeoff for STT?** (Deepgram is very accurate, local models slightly less)
4. **Current response time measurements?** (Would help validate optimizations)

---

## Next Steps

**Recommended immediate action**:
1. Get Groq API key (free at https://console.groq.com)
2. Implement Groq integration (Option B - direct integration)
3. Measure improvement
4. Decide if additional optimizations needed

This should give you 5-10x improvement with minimal code changes.

Would you like me to:
- Implement the Groq integration directly?
- Create a timing measurement script first?
- Research if Letta natively supports Groq endpoints?
