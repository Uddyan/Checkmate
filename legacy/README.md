# Legacy Code Archive

This directory contains code from previous versions of Checkmate that is **not part of the minimal one-probe scanner**.

## What's Here

### `probes/` - Multi-Probe Attack Modules
**Archived probes:**
- `dan.py` - DAN jailbreak attacks
- `encoding.py` - Encoding-based bypasses (Base16, Hex, ASCII85)
- `goodside.py` - Riley Goodside's attack techniques
- `realtoxicityprompts.py` - Toxic content generation tests
- `latentinjection.py` - Hidden instruction attacks
- `leakreplay.py` - Data leakage tests
- `continuation.py` - Completion-based attacks
- `promptinject.py` - Direct prompt injection
- `packagehallucination.py` - Package dependency attacks
- `malwaregen.py` - Malicious code generation

### `detectors/` - Additional Detectors
**Archived detectors:**
- `dan.py` - DAN/DUDE jailbreak detection
- `productkey.py` - Product key generation detection
- `specialwords.py` - Slur/inappropriate word detection
- `unsafe_content.py` - General unsafe content detection

### `presets/` - Old Preset Configs
**Archived presets:**
- `chatbot_basic.yaml` - Basic chatbot attacks (~15 probes)
- `rag_basic.yaml` - RAG system attacks (~12 probes)
- `agent_tools.yaml` - Agent/tool attacks (~10 probes)

### `configs/` - Example Configs for Other Targets
**Archived configs:**
- `openai_chatbot_example.yaml` - OpenAI API configuration
- `http_app_rag_example.yaml` - RAG system testing
- `smoke_test_example.yaml` - Generic smoke test template

### `phase2-database/` - Optional PostgreSQL Integration
Complete database integration for persisting runs and findings.

**Contents:**
- `checkmate/db/` - PostgreSQL client with schema
- `README.md` - Database integration docs

**Why archived:** Database is optional; minimal scanner uses file-based reports only.

### `phase5-vector-store/` - Optional Vector Store
Vector database framework for attack prompt corpus.

**Contents:**
- `checkmate/vector_store/` - VectorStore abstraction + PgVector backend
- `tools/` - Ingestion scripts
- `README.md` - Vector store docs

**Why archived:** Vector store is optional; minimal scanner uses hardcoded prompts only.

### `old-scripts/` - Test Scripts
Archived test shell scripts and experimental code.

---

## Why Archived?

The minimal Checkmate scanner focuses on **simplicity and clarity**:

**✅ ONE probe:** `SmokeTestProbe` (5 jailbreak prompts)  
**✅ ONE detector:** `MitigationBypass`  
**✅ ONE preset:** `smoke-test`  
**✅ ONE config:** `smoke_test_deepseek.yaml`  
**✅ ONE target:** DeepSeek local server  

This makes the codebase:
- **Simple** - Easy to understand in < 30 minutes
- **Focused** - One proven attack path
- **Extensible** - Easy to add features later

---

## Restoring Features

To add back any archived features:

1. **Move files back** from `legacy/` to their original locations
2. **Update presets** to include the probes/detectors
3. **Update configs** as needed
4. **Test thoroughly** before deployment

### Example: Restore Database Integration

```bash
# Move database code back
mv legacy/phase2-database/checkmate/db checkmate/

# Enable in config
database:
  enabled: true
  url: "postgresql://user:pass@localhost:5432/checkmate"

# Run as normal
python3 enterprise_checkmate.py run --config myconfig.yaml
```

### Example: Add More Probes

```bash
# Move specific probe back
cp legacy/probes/dan.py checkmate/probes/

# Update preset to include it
probes:
  - "smoke_test.SmokeTestProbe"
  - "dan.DanInTheWild"  # Added back
```

---

## Status

- **Archived:** December 3, 2025
- **Original functionality:** Validated and working before archival
- **All code preserved:** Nothing deleted, just moved for clarity

---

## Current Minimal Scanner

**Active files:**
```
checkmate/probes/smoke_test.py      ⭐ Only probe
checkmate/detectors/mitigation.py   ⭐ Only detector  
checkmate/presets/smoke_test.yaml   ⭐ Only preset
examples/configs/smoke_test_deepseek.yaml  ⭐ Only config
```

**Golden path command:**
```bash
python3 enterprise_checkmate.py run --config examples/configs/smoke_test_deepseek.yaml
```

**Result:** Simple, reliable security scan in seconds.

---

For questions or to discuss restoring features, refer to the implementation plan in the artifacts directory.
