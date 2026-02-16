# Claude CLI Skills - Quick Reference

Швидка шпаргалка для щоденного використання skills.

---

## Installation (One-Time Setup)

```bash
# Recommended: Auto-install script
bash .claude/skills-installer/claude_skills_auto_install.sh
exit
claude

# Verify
What Skills are available?
```

**Expected output**: 5 skills listed (frontend-code-review, typescript-checker, seo-analyzer, tailwind-validator, cloudflare-inspector)

---

## When to Use Which Skill?

| Your Task | Skill to Use | Example Prompt |
|-----------|--------------|----------------|
| React component code review | `frontend-code-review` | "Review this component for A11Y" |
| TypeScript `any` types audit | `typescript-checker` | "Find all any types in this file" |
| SEO for landing page | `seo-analyzer` | "Analyze SEO for index.html" |
| Tailwind classes optimization | `tailwind-validator` | "Review Tailwind usage here" |
| Cloudflare Worker script | `cloudflare-inspector` | "Audit this Worker for security" |
| Accessibility audit | `frontend-code-review` | "Check A11Y compliance" |
| JSON-LD structured data | `seo-analyzer` | "Review schema.org markup" |
| Dark mode Tailwind | `tailwind-validator` | "Check dark: prefix usage" |
| Cloudflare SSL config | `cloudflare-inspector` | "Review SSL/TLS settings" |
| tsconfig.json strict mode | `typescript-checker` | "Audit tsconfig for strict" |

---

## Quick Testing Snippets

### 1. Frontend Code Review

```tsx
// Test case: Accessibility issues
const BadButton = ({ onClick }) => (
  <div onClick={onClick} style={{ cursor: 'pointer' }}>
    Click me
  </div>
);

// Prompt: Review this React component for accessibility
```

**What skill should find**:
- `<div>` should be `<button>`
- No keyboard accessibility
- Missing ARIA attributes
- Style in JSX (should use className)

---

### 2. TypeScript Checker

```ts
// Test case: Unsafe types
function fetchData(url: string): any {
  return fetch(url).then(res => res.json());
}

const processData = (data: any) => {
  return data.map((item: any) => item.name);
};

// Prompt: Find and fix all type issues
```

**What skill should find**:
- `any` return type → `Promise<any>` → more specific type
- `any` parameter → proper interface/type
- Array method without type guard
- Missing null checks

---

### 3. SEO Analyzer

```html
<!-- Test case: Missing SEO essentials -->
<!DOCTYPE html>
<html>
  <head>
    <title></title>
  </head>
  <body>
    <div class="content">
      <p>Welcome to our site!</p>
      <img src="hero.jpg">
    </div>
  </body>
</html>

<!-- Prompt: Analyze this page for SEO issues -->
```

**What skill should find**:
- Empty `<title>`
- Missing meta description
- No H1 heading
- Image without alt text
- No structured data (JSON-LD)
- Missing Open Graph tags
- No canonical URL
- No language specification

---

### 4. Tailwind Validator

```tsx
// Test case: Tailwind anti-patterns
<div className="flex flex-row justify-center items-center p-4 padding-4 m-2 margin-2 text-sm text-lg text-blue-500 text-red-500 w-full width-100 invalid-class">
  <span className="font-bold font-weight-700">Hello</span>
</div>

// Prompt: Review Tailwind CSS usage
```

**What skill should find**:
- `flex-row` redundant (flex is row by default)
- `padding-4` invalid (not Tailwind class)
- `p-4` and `padding-4` duplicate
- `margin-2` invalid
- `text-sm` conflicts with `text-lg`
- `text-blue-500` conflicts with `text-red-500`
- `width-100` invalid
- `invalid-class` not in Tailwind
- `font-weight-700` invalid (use `font-bold`)

---

### 5. Cloudflare Inspector

```js
// Test case: Worker without error handling
addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
  );
});

// Prompt: Review this Cloudflare Worker for issues
```

**What skill should find**:
- No error handling (no try/catch)
- No CORS headers
- No logging for debugging
- No request validation
- Missing response headers (CSP, etc.)
- No timeout handling
- No rate limiting consideration

---

## Common Prompts Templates

### Code Review Workflow

```
1. Initial review:
   "Review this [component/file] using frontend-code-review skill"

2. TypeScript focus:
   "Check TypeScript types in this file"

3. SEO audit (for pages):
   "Analyze SEO for this HTML page"

4. Styling review:
   "Validate Tailwind CSS usage here"

5. Infrastructure (if using Cloudflare):
   "Review Cloudflare configuration"
```

---

### Specific Issue Investigation

```
# A11Y issues:
"Review accessibility of this component, focus on keyboard navigation and ARIA"

# Type safety:
"Find all places where we use 'any' type and suggest concrete types"

# SEO meta tags:
"Review all meta tags and suggest improvements for better search ranking"

# Tailwind optimization:
"Find redundant or conflicting Tailwind classes and suggest cleanup"

# Cloudflare security:
"Audit WAF rules and SSL/TLS configuration for security gaps"
```

---

### Before Production Deployment

```
1. "Run frontend-code-review on all components in src/components/"
2. "Check TypeScript strict mode compliance across the project"
3. "Analyze SEO for all public HTML pages (index, about, contact)"
4. "Validate Tailwind usage for bundle size optimization"
5. "Review Cloudflare caching strategy and security settings"
```

---

## Skill Capabilities Summary

### frontend-code-review

**Checks**:
- ✅ HTML semantics
- ✅ CSS quality and organization
- ✅ JavaScript/TypeScript code
- ✅ Accessibility (WCAG AA/AAA)
- ✅ Performance (bundle, lazy loading)
- ✅ Security (XSS, CSRF, secrets)

**Best for**:
- PR code reviews
- Component audits
- Accessibility compliance
- Security audits

---

### typescript-checker

**Checks**:
- ⚠️ `any` types detection
- ✅ Type safety (union, intersection)
- ✅ Null safety (strictNullChecks)
- ✅ Function signatures
- ✅ Advanced types (mapped, conditional)
- ⚙️ tsconfig.json optimization

**Best for**:
- Type migration (JS → TS)
- Strict mode enablement
- Type error debugging
- Code quality improvement

---

### seo-analyzer

**Checks**:
- 🏷️ Meta tags (title, description, robots)
- 📝 Content structure (H1-H6)
- 📊 Structured data (JSON-LD, OG)
- 📱 Technical SEO (mobile, HTTPS)
- 🔗 Content quality (keywords, links)

**Best for**:
- Landing page optimization
- Multilingual sites (hreflang)
- Schema.org markup
- Search ranking improvement

---

### tailwind-validator

**Checks**:
- ✅ Class validity
- 🧹 Redundant/conflicting classes
- 📱 Responsive design (breakpoints)
- 🌗 Dark mode implementation
- ⚙️ tailwind.config.js
- 📦 Bundle optimization

**Best for**:
- Component styling review
- Bundle size optimization
- Responsive design audit
- Dark mode implementation

---

### cloudflare-inspector

**Checks**:
- 🌐 DNS configuration
- 💾 Caching strategy
- 🔒 SSL/TLS security
- 🛡️ WAF and DDoS protection
- 📄 Page Rules / Redirects
- ⚡ Workers scripts

**Best for**:
- Infrastructure setup
- Security hardening
- Performance optimization
- Worker script review

---

## Troubleshooting Quick Fixes

### Skills not showing

```bash
# 1. Check files exist
ls -la ~/.claude/skills/*/SKILL.md

# 2. Restart Claude CLI
exit
claude

# 3. Verify YAML format
head -5 ~/.claude/skills/frontend-code-review/SKILL.md
```

---

### Skill not activating

```
# Instead of vague prompt:
"Review this code"  ❌

# Use specific skill reference:
"Use frontend-code-review skill to review this component"  ✅
```

---

### Wrong skill activating

```
# Be explicit about skill:
"Use typescript-checker skill to find all any types in this file"

# Or specify multiple:
"Use frontend-code-review and tailwind-validator skills to review this React component"
```

---

## Integration with Development Workflow

### Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running Claude Skills check..."
claude "Review staged files using frontend-code-review and typescript-checker skills"
```

---

### CI/CD Integration

```yaml
# .github/workflows/code-review.yml
name: Claude Skills Review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Claude Code Review
        run: |
          claude "Review PR changes using all applicable skills"
```

---

### IDE Integration

**VSCode** (example):

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Claude: Review Current File",
      "type": "shell",
      "command": "claude 'Review ${file} using frontend-code-review skill'"
    }
  ]
}
```

---

## Keyboard Shortcuts (Example Setup)

Create aliases in `~/.bashrc` or `~/.zshrc`:

```bash
# Quick skill invocations
alias cr-frontend="claude 'Review this using frontend-code-review skill:'"
alias cr-ts="claude 'Check TypeScript types:'"
alias cr-seo="claude 'Analyze SEO:'"
alias cr-tailwind="claude 'Validate Tailwind:'"
alias cr-cf="claude 'Review Cloudflare config:'"

# Usage:
# cr-frontend src/components/Button.tsx
```

---

## Tips & Best Practices

1. **Be specific**: Instead of "review this", say "review for A11Y issues"
2. **Mention skill explicitly**: "Use frontend-code-review skill..."
3. **Combine skills**: "Use frontend-code-review and typescript-checker..."
4. **Provide context**: "This is a React form component, review for..."
5. **Ask for specific output**: "List issues as numbered list with priority"

---

## Resources

- Full documentation: `.claude/skills-installer/README.md`
- Step-by-step setup: `.claude/skills-installer/claude_skills_setup_prompt.md`
- Validation checklist: `.claude/skills-installer/claude_skills_checklist.md`
- Files overview: `.claude/skills-installer/FILES_OVERVIEW.md`

---

**Last updated**: 2025-12-28
**Version**: 1.0
