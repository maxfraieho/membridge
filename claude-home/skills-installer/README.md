# Claude CLI Skills Setup

Набір з 5 спеціалізованих skills для Claude CLI:

1. **frontend-code-review** - Аналіз HTML/CSS/JS/React коду
2. **typescript-checker** - TypeScript типова безпека
3. **seo-analyzer** - SEO аудит HTML сторінок
4. **tailwind-validator** - Tailwind CSS валідація
5. **cloudflare-inspector** - Cloudflare конфігурація та Workers

## Швидкий старт (Рекомендований)

```bash
bash .claude/skills-installer/claude_skills_auto_install.sh
exit
claude
What Skills are available?
```

Очікуваний результат: всі 5 skills у списку.

---

## Структура після встановлення

### Global Installation (Option A)
```
~/.claude/skills/
├── frontend-code-review/SKILL.md
├── typescript-checker/SKILL.md
├── seo-analyzer/SKILL.md
├── tailwind-validator/SKILL.md
└── cloudflare-inspector/SKILL.md
```

### Project-Local Installation (Option C)
```
violin.pp.ua/.claude/skills/
├── frontend-code-review/SKILL.md
├── typescript-checker/SKILL.md
├── seo-analyzer/SKILL.md
├── tailwind-validator/SKILL.md
└── cloudflare-inspector/SKILL.md
```

---

## Детальний опис skills

### 1. frontend-code-review

**Призначення**: Комплексний аналіз frontend коду на якість, доступність та продуктивність.

**Що перевіряє**:
- ✅ HTML семантика (header/nav/main/article)
- ✅ CSS структура, адаптивність, дублікати
- ✅ JavaScript/TypeScript якість коду
- ✅ Доступність (A11Y): ARIA, контраст, keyboard nav
- ✅ Продуктивність: bundle size, lazy loading
- ✅ Безпека: XSS, CSP, secrets

**Приклади використання**:
```
Review this React component for accessibility and performance
Check this HTML/CSS for best practices
Analyze this Vue.js app for security issues
```

**Коли використовувати**:
- Після створення нового компоненту
- Перед production deploy
- Code review PR
- Рефакторинг legacy коду

---

### 2. typescript-checker

**Призначення**: Аудит TypeScript коду на типову безпеку та конфігурацію.

**Що перевіряє**:
- ⚠️ Виявлення `any` типів (пропонує конкретні типи)
- ✅ Union/intersection types правильність
- ✅ Null safety (strictNullChecks, optional chaining)
- ✅ Function signatures, return types
- ✅ Advanced types (mapped, conditional, utility)
- ⚙️ tsconfig.json налаштування

**Приклади використання**:
```
Find and fix all any types in this file
Check this TypeScript project for type safety issues
Review tsconfig.json configuration
```

**Коли використовувати**:
- Міграція з JavaScript на TypeScript
- Увімкнення strict mode
- Code review з фокусом на типи
- Debugging type errors

---

### 3. seo-analyzer

**Призначення**: SEO аудит HTML сторінок для кращої індексації пошуковими системами.

**Що перевіряє**:
- 🏷️ Meta tags (title, description, robots, canonical)
- 📝 Content структура (H1-H6 ієрархія)
- 📊 Structured data (JSON-LD, Open Graph, Twitter Cards)
- 📱 Technical SEO (mobile-friendly, HTTPS, Core Web Vitals)
- 🔗 Content якість (keywords, readability, internal links)

**Приклади використання**:
```
Analyze this HTML page for SEO issues and improvements
Review meta tags for this landing page
Check structured data implementation
```

**Коли використовувати**:
- Створення нових сторінок
- SEO оптимізація існуючих сторінок
- Multilingual sites (hreflang теги)
- Schema.org markup додавання

---

### 4. tailwind-validator

**Призначення**: Валідація Tailwind CSS використання та оптимізація.

**Що перевіряє**:
- ✅ Валідність Tailwind класів (тільки існуючі)
- 🧹 Надлишкові/дубльовані utility класи
- 📱 Responsive breakpoints (sm/md/lg/xl/2xl)
- 🌗 Dark mode (dark: префікси)
- ⚙️ tailwind.config.js конфігурація
- 📦 Bundle size оптимізація (purge налаштування)

**Приклади використання**:
```
Review this component for Tailwind CSS best practices
Optimize these Tailwind classNames
Validate tailwind.config.js setup
```

**Коли використовувати**:
- Створення нових компонентів з Tailwind
- Рефакторинг стилів
- Bundle size оптимізація
- Код review з фокусом на CSS

---

### 5. cloudflare-inspector

**Призначення**: Аудит Cloudflare конфігурації (DNS, CDN, Workers) для безпеки та продуктивності.

**Що перевіряє**:
- 🌐 DNS (A/AAAA/CNAME/MX/TXT, DNSSEC)
- 💾 Кешування (Cache Level, TTL, Cache Rules)
- 🔒 SSL/TLS (режим Full Strict, HSTS)
- 🛡️ WAF, DDoS, bot protection, rate limiting
- 📄 Page Rules / Redirect Rules / Transform Rules
- ⚡ Cloudflare Workers (routes, error handling, security)

**Приклади використання**:
```
Review my Cloudflare DNS and SSL configuration
Analyze this Cloudflare Worker script for issues
Audit WAF and security settings
```

**Коли використовувати**:
- Налаштування нового домену
- Аудит безпеки
- Workers deployment
- Оптимізація кешування

---

## Troubleshooting

### Skills не відображаються

**Проблема**: `What Skills are available?` не показує нові skills.

**Рішення**:
```bash
# 1. Перевірити чи існують файли
ls -la ~/.claude/skills/*/SKILL.md

# 2. Перевірити формат YAML front matter
head -5 ~/.claude/skills/frontend-code-review/SKILL.md
# Має бути:
# ---
# name: frontend-code-review
# description: ...
# ---

# 3. Перезапустити Claude CLI
exit
claude
```

---

### Помилка "Permission denied"

**Проблема**: `bash: Permission denied: claude_skills_auto_install.sh`

**Рішення**:
```bash
chmod +x .claude/skills-installer/claude_skills_auto_install.sh
bash .claude/skills-installer/claude_skills_auto_install.sh
```

---

### Skills конфліктують з вбудованими

**Проблема**: Вбудовані skills `frontend-code-review`, `typescript-checker` вже існують.

**Рішення**:
- User skills (`~/.claude/skills/`) мають **пріоритет** над вбудованими
- Це означає, що ваші кастомні skills **перезапишуть** вбудовані
- Якщо хочете зберегти обидва варіанти:
  1. Перейменуйте кастомні skills (наприклад, `frontend-code-review-extended`)
  2. Або використовуйте project-local skills (`.claude/skills/` в проекті)

---

## Додаткові файли

- **claude_skills_setup_prompt.md** - Покрокова ручна інсталяція
- **claude_skills_checklist.md** - Чекліст валідації
- **quick_install.sh** - Скорочений інстал (без детальних описів)
- **QUICK_REFERENCE.md** - Шпаргалка для щоденного використання
- **skills_manifest.json** - Опис skills у JSON форматі
- **FILES_OVERVIEW.md** - Огляд всіх файлів

---

## Коли який skill використовувати?

| Завдання                              | Skill                   |
|--------------------------------------|-------------------------|
| React компонент code review          | frontend-code-review    |
| TypeScript `any` типи                | typescript-checker      |
| SEO мета-теги для landing page       | seo-analyzer            |
| Tailwind класи оптимізація           | tailwind-validator      |
| Cloudflare Worker скрипт аналіз      | cloudflare-inspector    |
| Доступність (A11Y) аудит             | frontend-code-review    |
| JSON-LD structured data              | seo-analyzer            |
| Dark mode Tailwind                   | tailwind-validator      |
| Cloudflare SSL/TLS налаштування      | cloudflare-inspector    |
| tsconfig.json strict режим           | typescript-checker      |

---

## Мінімальні тести

### 1. Frontend Code Review
```tsx
// Test: React component with A11Y issues
const BadButton = () => <div onClick={() => alert('click')}>Click me</div>;
// Очікування: skill має знайти проблеми з семантикою та keyboard nav
```

### 2. TypeScript Checker
```ts
// Test: Unsafe any usage
function getData(): any { return fetch('/api'); }
// Очікування: skill має запропонувати конкретний тип (Promise<Response>)
```

### 3. SEO Analyzer
```html
<!-- Test: Missing meta tags -->
<html><head><title></title></head><body>Content</body></html>
<!-- Очікування: skill має знайти відсутні meta description, H1 -->
```

### 4. Tailwind Validator
```tsx
// Test: Invalid/redundant classes
<div className="flex flex-row p-4 padding-4 invalid-class">
// Очікування: flex-row redundant (flex за замовчуванням row), invalid-class не існує
```

### 5. Cloudflare Inspector
```js
// Test: Cloudflare Worker without error handling
addEventListener('fetch', event => {
  event.respondWith(fetch(event.request)); // No try/catch
});
// Очікування: skill має запропонувати додати error handling
```

---

## Версії та оновлення

**Поточна версія**: 1.0 (2025-12-28)

**Зміни в версіях**:
- v1.0 (2025-12-28) - Початковий реліз з 5 skills

**Оновлення skills**:
```bash
# Backup існуючих
cp -r ~/.claude/skills ~/.claude/skills.backup

# Перезапуск інсталяції
bash .claude/skills-installer/claude_skills_auto_install.sh
```

---

## Ліцензія

MIT License - вільне використання в особистих та комерційних проектах.

---

## Підтримка

**Питання та проблеми**:
1. Перевірте checklist: `.claude/skills-installer/claude_skills_checklist.md`
2. Перегляньте troubleshooting секцію вище
3. Створіть issue в репозиторії проекту

**Покращення та доповнення**:
- Skills можна розширювати додаванням нових перевірок
- Кожен SKILL.md файл можна редагувати вручну
- Додавайте власні приклади використання
