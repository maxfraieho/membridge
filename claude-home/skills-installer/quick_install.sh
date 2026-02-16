#!/bin/bash
set -e

SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$SKILLS_DIR"

echo "🚀 Quick Install - 5 Claude CLI Skills"
echo "Target: $SKILLS_DIR"
echo

# Frontend Code Review
echo "▶️ [1/5] frontend-code-review"
mkdir -p "$SKILLS_DIR/frontend-code-review"
cat > "$SKILLS_DIR/frontend-code-review/SKILL.md" << 'SKILL1'
---
name: frontend-code-review
description: Проводить детальний review frontend коду (HTML/CSS/JS, React/Vue/Svelte) на відповідність найкращим практикам, A11Y, продуктивність та безпеку.
---

# Frontend Code Review Skill

Аналізує frontend код за категоріями:

## HTML Семантика
- Правильне використання semantic tags (header/nav/main/article/footer/aside)
- Структура документу та ієрархія заголовків
- Використання ARIA атрибутів там, де потрібно

## CSS Якість
- Організація стилів (БЕМ/SMACSS/Atomic)
- Адаптивність та mobile-first підхід
- Дублікати та оптимізація розміру
- CSS Grid та Flexbox правильне використання

## JavaScript/TypeScript
- Обробка помилок (try/catch, error boundaries)
- Валідація вводу користувача
- Асинхронний код (async/await, promises)
- Уникнення memory leaks

## Доступність (A11Y)
- Клавіатурна навігація (tabindex, focus)
- ARIA roles, labels, descriptions
- Контрастність кольорів (WCAG AA/AAA)
- Screen reader сумісність

## Продуктивність
- Bundle size аналіз
- Lazy loading компонентів та зображень
- Code splitting стратегії
- Rendering performance (React.memo, useMemo)

## Безпека
- XSS захист (sanitization, CSP)
- CSRF токени
- Secrets не в коді (API keys, tokens)
- Безпечні dependencies (npm audit)

Використання:
- Review this React component for accessibility and performance
- Check this HTML/CSS for best practices
- Analyze this Vue.js app for security issues
SKILL1
echo "✓ frontend-code-review"

# TypeScript Checker
echo "▶️ [2/5] typescript-checker"
mkdir -p "$SKILLS_DIR/typescript-checker"
cat > "$SKILLS_DIR/typescript-checker/SKILL.md" << 'SKILL2'
---
name: typescript-checker
description: Перевіряє TypeScript код на типові помилки, unsafe any та strict режим.
---

# TypeScript Checker Skill

Спеціалізується на аналізі TypeScript коду:

## Type Safety
- Виявлення `any` типів та пропозиції конкретних типів
- Union та intersection types правильне використання
- Generic constraints та type inference
- Type guards та type predicates

## Null Safety
- strictNullChecks відповідність
- Optional chaining (?.) та nullish coalescing (??)
- Non-null assertion (!) аудит
- Undefined vs null consistency

## Function Types
- Return types явні оголошення
- Function overloads правильність
- Void vs undefined
- Never type використання

## Advanced Types
- Mapped types (Partial, Required, Pick, Omit)
- Conditional types
- Template literal types
- Utility types з @types

## tsconfig.json
- strict режим увімкнено
- noImplicitAny, strictNullChecks
- esModuleInterop, allowSyntheticDefaultImports
- Paths aliases та baseUrl

Використання:
- Find and fix all any types in this file
- Review TypeScript project for type safety
- Check tsconfig.json configuration
SKILL2
echo "✓ typescript-checker"

# SEO Analyzer
echo "▶️ [3/5] seo-analyzer"
mkdir -p "$SKILLS_DIR/seo-analyzer"
cat > "$SKILLS_DIR/seo-analyzer/SKILL.md" << 'SKILL3'
---
name: seo-analyzer
description: Аналізує HTML сторінки на SEO (мета-теги, структура, контент).
---

# SEO Analyzer Skill

Комплексний SEO аудит:

## Meta Tags
- Title унікальний та описовий (50-60 символів)
- Meta description (150-160 символів)
- Robots directives (index, follow, noarchive)
- Canonical URL для уникнення дублікатів

## Content Structure
- H1 унікальний на сторінці
- H2-H6 логічна ієрархія
- Alt теги для зображень
- Internal та external linking стратегія

## Structured Data
- JSON-LD Schema.org markup
- Open Graph для соцмереж
- Twitter Cards
- Breadcrumbs markup

## Technical SEO
- Mobile-friendly (viewport meta, responsive)
- HTTPS використання
- Core Web Vitals (LCP, FID, CLS концепції)
- Sitemap.xml та robots.txt

## Content Quality
- Keyword density (не spam)
- Readability score (Flesch-Kincaid)
- Content uniqueness
- Internal links distribution

Використання:
- Analyze this HTML page for SEO issues
- Review meta tags for landing page
- Check structured data implementation
SKILL3
echo "✓ seo-analyzer"

# Tailwind Validator
echo "▶️ [4/5] tailwind-validator"
mkdir -p "$SKILLS_DIR/tailwind-validator"
cat > "$SKILLS_DIR/tailwind-validator/SKILL.md" << 'SKILL4'
---
name: tailwind-validator
description: Перевіряє Tailwind CSS класи, responsive та конфігурацію.
---

# Tailwind Validator Skill

Валідація Tailwind CSS:

## Class Validity
- Тільки існуючі Tailwind utility класи
- Deprecated класи виявлення
- Custom classes відповідність tailwind.config.js

## Class Organization
- Надлишкові класи (дублікати)
- Конфліктуючі utility класи
- Групування по категоріях (layout/typography/colors)

## Responsive Design
- Breakpoints правильність (sm/md/lg/xl/2xl)
- Mobile-first підхід
- Container та max-width usage

## States & Variants
- Hover/focus/active стани
- Dark mode (dark: prefix)
- Group та peer модифікатори
- Arbitrary values ([], ()) використання

## Configuration
- tailwind.config.js completeness
- Content paths правильність (purge)
- Theme customization (colors, fonts, spacing)
- Plugins (forms, typography, aspect-ratio)

## Bundle Optimization
- Unused classes potential
- JIT mode використання
- Safelist для dynamic classes

Використання:
- Review this component for Tailwind best practices
- Optimize these Tailwind classNames
- Validate tailwind.config.js setup
SKILL4
echo "✓ tailwind-validator"

# Cloudflare Inspector
echo "▶️ [5/5] cloudflare-inspector"
mkdir -p "$SKILLS_DIR/cloudflare-inspector"
cat > "$SKILLS_DIR/cloudflare-inspector/SKILL.md" << 'SKILL5'
---
name: cloudflare-inspector
description: Аналізує Cloudflare DNS, кешування, SSL/TLS, WAF та Workers.
---

# Cloudflare Inspector Skill

Комплексний аудит Cloudflare:

## DNS Configuration
- A/AAAA records правильність
- CNAME flattening
- MX records для email
- TXT records (SPF, DKIM, DMARC)
- TTL оптимізація
- DNSSEC увімкнено

## Caching
- Cache Level (Standard/Ignore Query String)
- Browser Cache TTL vs Edge Cache TTL
- Cache Everything page rule
- Bypass Cache for dynamic content
- Cache purge strategies

## SSL/TLS
- SSL mode (Off/Flexible/Full/Full Strict) ⚠️ Only Full Strict безпечний
- Edge Certificates validity
- Always Use HTTPS rule
- HTTP Strict Transport Security (HSTS)
- Minimum TLS version (1.2+)

## Security (WAF)
- Web Application Firewall rules
- DDoS protection settings
- Bot Fight Mode
- Rate Limiting rules
- Challenge Page customization

## Page Rules & Redirects
- Page Rules priority та overlaps
- Redirect Rules (301/302)
- Transform Rules (URL/Headers)
- Origin Rules

## Cloudflare Workers
- Routes binding правильність
- Environment variables безпека
- Error handling (try/catch)
- Response headers (CORS, CSP)
- Performance (CPU time limits)
- Logging та debugging

## Performance
- Auto Minify (HTML/CSS/JS)
- Brotli compression
- HTTP/2 та HTTP/3 (QUIC)
- Rocket Loader (JS async)
- Polish (image optimization)

Використання:
- Review my Cloudflare DNS and SSL config
- Analyze this Cloudflare Worker script
- Audit WAF and security settings
SKILL5
echo "✓ cloudflare-inspector"

echo
echo "✅ All 5 skills installed to $SKILLS_DIR"
echo
echo "Next steps:"
echo "  1. exit"
echo "  2. claude"
echo "  3. What Skills are available?"
