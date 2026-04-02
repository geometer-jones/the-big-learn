# TODOS

## Guided Reading

### Gemini Adaptive Scaffolding Parity

**What:** Bring the shared adaptive guided-reading prompt source and learner-style persistence contract to the Gemini host command after Codex and Claude land.

**Why:** Prevents host behavior drift and preserves the "same ritual across hosts" product claim.

**Context:** Scope was intentionally reduced to Codex plus Claude in this eng review. Gemini already has a host command path, so leaving parity undocumented makes future drift more likely. Start in `hosts/gemini/commands/the-big-learn/guided-reading.toml` after the shared prompt source and shared host-test refactor exist.

**Effort:** M
**Priority:** P2
**Depends on:** Shared prompt source and shared host-test refactor landing first

## Distribution

### One-Command Bootstrap Install

**What:** Add a one-command bootstrap path, likely `pipx install the-big-learn` or a release-backed installer, so technical users can reach the host-native guided-reading flow without repository gymnastics.

**Why:** The product promise starts inside Claude Code or Codex, but the current setup still feels like a repository project. This closes that gap without committing to the full layperson distribution story yet.

**Context:** This review intentionally kept distribution out of scope. The approved design doc still calls for a one-command bootstrap as the next productization step after the core ritual is proven. Start by targeting technical users only, not full layperson onboarding.

**Effort:** M
**Priority:** P2
**Depends on:** Adaptive persistence and shared host prompt generation landing first

## Integrations

### Optional Nostr Export For Chapter Reflections

**What:** Explore a future Nostr export or share layer for chapter-end `Personal Response` or study-journal posts, likely as `kind:1` text notes or a better-fit event type if richer semantics are needed later.

**Why:** Preserves the social or public-study idea without contaminating core learner persistence or forcing key and relay management into the guided-reading loop.

**Context:** During architecture review we explicitly rejected Nostr as core persistence because `kind:1` is the wrong shape for mutable learner state. The only sensible future fit is export or share, not internal storage. This should wait until the adaptive guided-reading core is stable and the chapter-end artifact is clearly worth exporting.

**Effort:** M
**Priority:** P3
**Depends on:** Adaptive guided-reading core shipping first

## Completed
