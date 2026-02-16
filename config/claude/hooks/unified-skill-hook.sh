#!/bin/bash
# Unified Claude CLI UserPromptSubmit Hook
# Combines: forced-eval + LLM-eval + simple-instruction
#
# Features:
# - Forced skill evaluation with YES/NO reasoning
# - Optional LLM-based skill selection (if ANTHROPIC_API_KEY set)
# - Mandatory 3-step workflow enforcement
# - Fallback to forced evaluation if API unavailable
#
# Installation: Copy to .claude/hooks/UserPromptSubmit

# ============================================================================
# CONFIGURATION
# ============================================================================
# Use the latest Haiku model for cost-effective evaluation
MODEL="claude-haiku-4-5-20251001"

# ============================================================================
# AVAILABLE SKILLS (embedded list - auto-updated from .claude/skills/)
# ============================================================================
SKILLS_LIST=(
    "algorithmic-art"
    "ast-grep"
    "brainstorming"
    "brand-guidelines"
    "canvas-design"
    "condition-based-waiting"
    "defense-in-depth"
    "dispatching-parallel-agents"
    "document-skills"
    "executing-plans"
    "finishing-a-development-branch"
    "frontend-design"
    "internal-comms"
    "mcp-builder"
    "receiving-code-review"
    "requesting-code-review"
    "root-cause-tracing"
    "sharing-skills"
    "skill-creator"
    "slack-gif-creator"
    "subagent-driven-development"
    "systematic-debugging"
    "template-skill"
    "test-driven-development"
    "testing-anti-patterns"
    "testing-skills-with-subagents"
    "theme-factory"
    "using-git-worktrees"
    "using-superpowers"
    "verification-before-completion"
    "web-artifacts-builder"
    "webapp-testing"
    "writing-plans"
    "writing-skills"
)

SKILL_DESCRIPTIONS=(
    "algorithmic-art: генеративне мистецтво, p5.js, flow fields"
    "ast-grep: структурний пошук коду через AST, аналіз патернів"
    "brainstorming: брейнсторм, проектування, ідеї перед кодингом"
    "brand-guidelines: корпоративний стиль Anthropic"
    "canvas-design: графіка на canvas, дизайн в PNG/PDF"
    "condition-based-waiting: очікування умов замість timeouts"
    "defense-in-depth: валідація на кількох рівнях системи"
    "dispatching-parallel-agents: паралельні агенти для незалежних задач"
    "document-skills: робота з Word, PDF, PowerPoint, Excel"
    "executing-plans: реалізація планів у контрольованих батчах"
    "finishing-a-development-branch: завершення розробки, merge/PR/cleanup"
    "frontend-design: дизайн інтерфейсів, production-grade UI"
    "internal-comms: внутрішні комунікації, звіти, оновлення"
    "mcp-builder: створення MCP серверів (FastMCP/TypeScript)"
    "receiving-code-review: прийом code review з верифікацією"
    "requesting-code-review: формування якісних code review"
    "root-cause-tracing: аналіз першопричин, трасування помилок"
    "sharing-skills: контрибуція skills через pull request"
    "skill-creator: створення нових skills"
    "slack-gif-creator: анімовані GIF для Slack"
    "subagent-driven-development: розробка з субагентами та code review"
    "systematic-debugging: 4-фазне дебагінг-мислення"
    "template-skill: базовий каркас для нової навички"
    "test-driven-development: TDD - тест спочатку, потім код"
    "testing-anti-patterns: уникнення анти-патернів у тестах"
    "testing-skills-with-subagents: тестування skills субагентами"
    "theme-factory: темізація артефактів, 10 готових тем"
    "using-git-worktrees: ізольовані git worktrees для feature work"
    "using-superpowers: обов'язкові workflows для пошуку skills"
    "verification-before-completion: верифікація перед завершенням"
    "web-artifacts-builder: складні React/Tailwind/shadcn компоненти"
    "webapp-testing: тестування веб-додатків через Playwright"
    "writing-plans: створення детальних планів імплементації"
    "writing-skills: TDD для створення skills"
)

# ============================================================================
# INPUT PARSING
# ============================================================================
INPUT_JSON=$(timeout 2 cat 2>/dev/null || echo '{}')
USER_PROMPT=$(echo "$INPUT_JSON" | jq -r '.prompt // ""' 2>/dev/null)
CWD=$(echo "$INPUT_JSON" | jq -r '.cwd // ""' 2>/dev/null)

if [ -z "$CWD" ] || [ "$CWD" = "null" ]; then
    CWD="${CLAUDE_PROJECT_DIR:-.}"
fi

# ============================================================================
# LLM EVALUATION (if API key available)
# ============================================================================
LLM_SELECTED_SKILLS=()

if [ -n "$ANTHROPIC_API_KEY" ] && [ -n "$USER_PROMPT" ]; then
    # Build skills list for LLM
    AVAILABLE_SKILLS=""
    for desc in "${SKILL_DESCRIPTIONS[@]}"; do
        AVAILABLE_SKILLS="${AVAILABLE_SKILLS}- ${desc}\n"
    done

    # Prepare evaluation prompt
    EVAL_PROMPT=$(cat <<EOF
Return ONLY a JSON array of skill names that match this request.
Request: ${USER_PROMPT}
Skills:
${AVAILABLE_SKILLS}
Format: ["skill-name"] or []
EOF
)

    # Call Claude API
    RESPONSE=$(curl -s --max-time 5 https://api.anthropic.com/v1/messages \
        -H "content-type: application/json" \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -d "{
            \"model\": \"$MODEL\",
            \"max_tokens\": 200,
            \"temperature\": 0,
            \"system\": \"You are a skill matcher. Return only valid JSON arrays.\",
            \"messages\": [{
                \"role\": \"user\",
                \"content\": $(echo "$EVAL_PROMPT" | jq -Rs .)
            }]
        }" 2>/dev/null)

    # Extract skills from response
    if [ -n "$RESPONSE" ]; then
        RAW_TEXT=$(echo "$RESPONSE" | jq -r '.content[0].text' 2>/dev/null)
        
        if [ -n "$RAW_TEXT" ] && [ "$RAW_TEXT" != "null" ]; then
            # Strip markdown fences and extract JSON
            SKILLS=$(echo "$RAW_TEXT" | sed -n '/^\[/,/^\]/p' | head -n 1)
            
            if [ -z "$SKILLS" ]; then
                SKILLS="$RAW_TEXT"
            fi
            
            # Parse skills array
            SKILL_COUNT=$(echo "$SKILLS" | jq 'length' 2>/dev/null)
            
            if [ -n "$SKILL_COUNT" ] && [ "$SKILL_COUNT" != "null" ] && [ "$SKILL_COUNT" != "0" ]; then
                while IFS= read -r skill; do
                    LLM_SELECTED_SKILLS+=("$skill")
                done < <(echo "$SKILLS" | jq -r '.[]' 2>/dev/null)
            fi
        fi
    fi
fi

# ============================================================================
# MANDATORY INSTRUCTION OUTPUT
# ============================================================================
cat <<'INSTRUCTION_END'
INSTRUCTION: MANDATORY SKILL ACTIVATION SEQUENCE

Step 1 - EVALUATE (do this in your response):
For each skill in <available_skills>, state: [skill-name] - YES/NO - [reason]

INSTRUCTION_END

# Output forced evaluation format
echo "Available skills for evaluation:"
for skill in "${SKILLS_LIST[@]}"; do
    echo "- $skill"
done
echo ""

cat <<'INSTRUCTION_END'
Step 2 - ACTIVATE (do this immediately after Step 1):
IF any skills are YES → Use Skill(skill-name) tool for EACH relevant skill NOW
IF no skills are YES → State "No skills needed" and proceed

Step 3 - IMPLEMENT:
Only after Step 2 is complete, proceed with implementation.

CRITICAL: You MUST call Skill() tool in Step 2. Do NOT skip to implementation.
The evaluation (Step 1) is WORTHLESS unless you ACTIVATE (Step 2) the skills.

Example of correct sequence:
- research: NO - not a research task
- svelte5-runes: YES - need reactive state
- sveltekit-structure: YES - creating routes

[Then IMMEDIATELY use Skill() tool:]
> Skill(svelte5-runes)
> Skill(sveltekit-structure)

[THEN and ONLY THEN start implementation]

INSTRUCTION_END

# If LLM selected skills, add mandatory activation notice
if [ ${#LLM_SELECTED_SKILLS[@]} -gt 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "LLM PRE-EVALUATION: The following skills were identified as relevant:"
    echo ""
    for skill in "${LLM_SELECTED_SKILLS[@]}"; do
        echo "  ✓ $skill"
    done
    echo ""
    echo "YOU MUST include these in your Step 1 evaluation as YES."
    echo "YOU MUST activate them in Step 2 using Skill() before implementation."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

exit 0
