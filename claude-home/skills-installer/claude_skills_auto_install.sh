#!/bin/bash
#
# Claude CLI Skills Auto Installer
# Встановлює всі 5 skills: frontend-code-review, typescript-checker, seo-analyzer, tailwind-validator, cloudflare-inspector
#
set -e

SKILLS_DIR="$HOME/.claude/skills"
echo "📦 Встановлення Claude Skills у: $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"

echo "▶️ [1/5] frontend-code-review"
mkdir -p "$SKILLS_DIR/frontend-code-review"
cat > "$SKILLS_DIR/frontend-code-review/SKILL.md" << 'EOF'
---
name: frontend-code-review
description: Проводить детальний review frontend коду (HTML/CSS/JS, React/Vue/Svelte) на відповідність найкращим практикам, доступність (A11Y), продуктивність та безпеку.
---

# Frontend Code Review Skill

Перевіряє:
- Семантику HTML (header/nav/main/article/footer)
- CSS структуру, адаптивність, дублікати
- Якість JS/TS, обробку помилок, валідацію вводу
- A11Y (ARIA, контраст, клавіатурна навігація)
- Продуктивність (bundle, lazy‑loading, зображення)
- Безпеку (XSS, CSP, secrets)

Приклади:
- Review this React component for accessibility and performance
- Check this HTML/CSS for best practices
EOF
echo "✓ frontend-code-review"

echo "▶️ [2/5] typescript-checker"
mkdir -p "$SKILLS_DIR/typescript-checker"
cat > "$SKILLS_DIR/typescript-checker/SKILL.md" << 'EOF'
---
name: typescript-checker
description: Перевіряє TypeScript код на типові помилки, unsafe any, strict режим та покращення tsconfig.
---

# TypeScript Checker Skill

Перевіряє:
- Використання any та пропонує конкретні типи
- Типову безпеку, union/intersection, generics
- Null/undefined (strictNullChecks, optional chaining)
- Сигнатури функцій, return type, overloads
- Advanced типи (mapped, conditional, utility)
- tsconfig (strict, noImplicitAny, strictNullChecks)

Приклади:
- Find and fix all any types in this file
- Check this TypeScript project for type safety issues
EOF
echo "✓ typescript-checker"

echo "▶️ [3/5] seo-analyzer"
mkdir -p "$SKILLS_DIR/seo-analyzer"
cat > "$SKILLS_DIR/seo-analyzer/SKILL.md" << 'EOF'
---
name: seo-analyzer
description: Аналізує HTML сторінки на SEO: мета-теги, заголовки, структуровані дані, технічну SEO та читабельність.
---

# SEO Analyzer Skill

Перевіряє:
- Title, meta description, robots, canonical
- H1–H6 ієрархію та структуру контенту
- JSON-LD/Schema.org, Open Graph, Twitter Cards
- Mobile-friendly, HTTPS, Core Web Vitals (концептуально)
- Щільність ключових слів, читабельність, internal links
- 404, broken links, duplicate content (надані фрагменти)

Приклади:
- Analyze this HTML page for SEO issues and improvements
- Review meta tags for this landing page
EOF
echo "✓ seo-analyzer"

echo "▶️ [4/5] tailwind-validator"
mkdir -p "$SKILLS_DIR/tailwind-validator"
cat > "$SKILLS_DIR/tailwind-validator/SKILL.md" << 'EOF'
---
name: tailwind-validator
description: Перевіряє використання Tailwind CSS: валідність класів, організацію, responsive breakpoints, dark mode та оптимізацію.
---

# Tailwind Validator Skill

Перевіряє:
- Чи використовуються лише валідні Tailwind класи
- Надлишкові / дубльовані utility‑класи
- Breakpoints (sm/md/lg/xl/2xl), mobile‑first
- Стані hover/focus/active, dark: префікси
- Налаштування tailwind.config.js (content, theme, plugins)
- Потенційний розмір CSS та purge налаштування

Приклади:
- Review this component for Tailwind CSS best practices
- Optimize these Tailwind classNames
EOF
echo "✓ tailwind-validator"

echo "▶️ [5/5] cloudflare-inspector"
mkdir -p "$SKILLS_DIR/cloudflare-inspector"
cat > "$SKILLS_DIR/cloudflare-inspector/SKILL.md" << 'EOF'
---
name: cloudflare-inspector
description: Аналізує Cloudflare конфігурацію: DNS, кешування, SSL/TLS, WAF, Rules та Workers для продуктивності й безпеки.
---

# Cloudflare Inspector Skill

Перевіряє:
- DNS (A/AAAA/CNAME/MX/TXT, TTL, DNSSEC)
- Кеш (Cache Level, Browser/Edge TTL, Cache Everything)
- SSL/TLS режим (Off/Flexible/Full/Full Strict)
- WAF, DDoS, bot protection, rate limiting
- Page Rules / Redirect Rules / Transform Rules (надані приклади)
- Workers: routes, environment, типові баги в логіці

Приклади:
- Review my Cloudflare DNS and SSL configuration
- Analyze this Cloudflare Worker script for issues
EOF
echo "✓ cloudflare-inspector"

echo
echo "✅ Встановлено skills в $SKILLS_DIR"
echo "Тепер: exit && claude, потім: What Skills are available?"
