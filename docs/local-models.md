# Local Model Setup

> How to run agents against locally hosted models instead of the Anthropic API.
> Advisor strategy is Anthropic-only — it is automatically disabled for local profiles.

---

## How it works

Claude Code supports `ANTHROPIC_API_URL` to point at any OpenAI-compatible endpoint.
Both Ollama and LM Studio expose this interface, so the same agent definitions
work locally — just with different model strings and no advisor tool.

`make configure PROFILE=<profile>` handles everything:
- Patches agent frontmatter with the correct model strings
- Removes the advisor tool section from agent files
- Writes `.env.claude` with the `ANTHROPIC_API_URL` export
- Updates the Active Model Config section in `CLAUDE.md`

---

## Ollama

### Install and start

```bash
# Install (macOS)
brew install ollama

# Start the server
ollama serve

# Pull models (examples)
ollama pull qwen2.5-coder:32b   # planning/review tier
ollama pull qwen2.5-coder:14b   # implement tier
ollama pull qwen2.5-coder:7b    # fast tier
ollama pull llama3.3:70b        # alternative
```

### Configure and activate

```bash
# Switch to Ollama profile
make configure PROFILE=ollama-qwen

# Activate the URL override in your current shell
source .env.claude

# Verify
echo $ANTHROPIC_API_URL   # should be http://localhost:11434/v1

# Run Claude Code — it will now hit Ollama
claude
```

### Model recommendations

| Task | Good options |
|------|-------------|
| Planning (Opus tier) | `qwen2.5-coder:32b`, `llama3.3:70b` |
| Implementation | `qwen2.5-coder:14b`, `llama3.3:70b` |
| Fast tasks | `qwen2.5-coder:7b`, `llama3.2:3b` |

Edit `config/models.json` under the `ollama-qwen` profile to use different models,
then re-run `make configure PROFILE=ollama-qwen`.

---

## LM Studio

### Install and start

1. Download LM Studio from https://lmstudio.ai
2. Download a model (GGUF format, e.g. Qwen2.5-Coder-14B-Instruct)
3. Go to **Local Server** tab → click **Start Server** (default port: 1234)
4. Load a model in the server tab

### Configure and activate

```bash
# Edit config/models.json — update the lmstudio profile model strings
# to match whatever model you have loaded in LM Studio
make configure PROFILE=lmstudio

source .env.claude

# Verify
echo $ANTHROPIC_API_URL   # should be http://localhost:1234/v1
```

---

## Custom OpenAI-compatible endpoint

Any endpoint that speaks the OpenAI Chat Completions API works.
Edit `config/models.json` directly:

```json
{
  "provider": "openai_compatible",
  "base_url": "https://your-endpoint/v1",
  "models": {
    "planning":  "your-model-id",
    "review":    "your-model-id",
    "implement": "your-model-id",
    "fast":      "your-model-id"
  },
  "advisor": { "enabled": false }
}
```

Then: `make configure && source .env.claude`

---

## Switching back to Anthropic

```bash
make configure PROFILE=anthropic-default
source .env.claude
# ANTHROPIC_API_URL is now unset (or not exported), Anthropic API resumes
```

---

## What the advisor strategy adds (Anthropic only)

When using the `anthropic-default` or `anthropic-budget` profiles, the developer
agent gets the `advisor_20260301` tool. Sonnet runs the full task and calls Opus
only when it hits something it can't reasonably resolve.

Benchmark results (from Anthropic):
- Sonnet + Opus advisor: +2.7pp on SWE-bench Multilingual vs Sonnet alone
- Cost: 11.9% *lower* than Sonnet alone (Opus only generates ~400-700 tokens per call)
- Haiku + Opus advisor: 41.2% on BrowseComp vs 19.7% Haiku alone

The `max_uses: 3` cap in `config/models.json` controls cost. Lower it for
high-volume batch tasks; raise it for complex architecture work.

---

## Tradeoffs

| | Anthropic API | Local (Ollama/LM Studio) |
|-|---------------|--------------------------|
| Advisor strategy | ✅ enabled | ❌ not available |
| Quality (frontier) | ✅ best | depends on model/hardware |
| Cost | per-token | compute (local) |
| Privacy | data leaves machine | fully local |
| Speed | network latency | depends on hardware |
| Offline | ❌ | ✅ |

Pick the profile that fits your current task. Switch anytime with `make configure`.
