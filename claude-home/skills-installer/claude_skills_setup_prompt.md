# Claude Skills Setup - Покрокова інструкція

Детальна інструкція для ручної інсталяції skills без автоматичних скриптів.

---

## Етап 1: Перевірка середовища

### 1.1 Перевірка Claude CLI

```bash
claude --version
```

**Очікуваний результат**: версія Claude CLI (наприклад, `1.2.3`)

**Якщо команда не знайдена**:
- Встановіть Claude CLI: https://docs.anthropic.com/claude/docs/claude-cli
- Або використовуйте `npm install -g @anthropic-ai/claude-cli`

---

### 1.2 Перевірка директорії `.claude`

```bash
ls -la ~/.claude/
```

**Очікуваний результат**: директорія існує з файлами налаштувань

**Якщо директорія не існує**:
```bash
mkdir -p ~/.claude/
```

---

### 1.3 Перевірка існуючих skills

```bash
ls -la ~/.claude/skills/ 2>/dev/null || echo "Skills directory does not exist"
```

**Якщо директорія не існує**:
```bash
mkdir -p ~/.claude/skills/
```

**Якщо skills вже існують**:
- Зробіть backup: `cp -r ~/.claude/skills ~/.claude/skills.backup.$(date +%Y%m%d)`
- Або видаліть старі: `rm -rf ~/.claude/skills/*`

---

## Етап 2: Створення директорій для skills

### 2.1 Створення структури

```bash
mkdir -p ~/.claude/skills/frontend-code-review
mkdir -p ~/.claude/skills/typescript-checker
mkdir -p ~/.claude/skills/seo-analyzer
mkdir -p ~/.claude/skills/tailwind-validator
mkdir -p ~/.claude/skills/cloudflare-inspector
```

### 2.2 Перевірка створення

```bash
ls -la ~/.claude/skills/
```

**Очікуваний результат**: 5 порожніх директорій

---

## Етап 3: Створення SKILL.md файлів

### 3.1 Frontend Code Review

```bash
cat > ~/.claude/skills/frontend-code-review/SKILL.md << 'EOF'
---
name: frontend-code-review
description: Проводить детальний review frontend коду (HTML/CSS/JS, React/Vue/Svelte) на відповідність найкращим практикам, доступність (A11Y), продуктивність та безпеку.
---

# Frontend Code Review Skill

Комплексний аналіз frontend коду за категоріями:

## HTML Семантика
- Правильне використання semantic tags (header/nav/main/article/footer/aside)
- Структура документу та ієрархія заголовків (H1-H6)
- Використання ARIA атрибутів там, де потрібно (але не зловживання)
- Form елементи з правильними labels та accessibility

## CSS Якість
- Організація стилів (БЕМ/SMACSS/Atomic CSS)
- Адаптивність та mobile-first підхід
- Дублікати та можливості оптимізації розміру
- CSS Grid та Flexbox правильне використання
- CSS Variables для theme management
- Animations та transitions performance

## JavaScript/TypeScript
- Обробка помилок (try/catch, error boundaries в React)
- Валідація вводу користувача (XSS prevention)
- Асинхронний код (async/await, promises, error handling)
- Уникнення memory leaks (event listeners, timers, subscriptions)
- Proper cleanup в useEffect hooks (React)
- State management patterns

## Доступність (A11Y)
- Клавіатурна навігація (tabindex, focus management)
- ARIA roles, labels, descriptions правильність
- Контрастність кольорів (WCAG AA/AAA відповідність)
- Screen reader сумісність
- Focus indicators visibility
- Skip links для навігації

## Продуктивність
- Bundle size аналіз та tree-shaking
- Lazy loading компонентів та зображень
- Code splitting стратегії (route-based, component-based)
- Rendering performance (React.memo, useMemo, useCallback)
- Image optimization (formats, sizes, lazy loading)
- Web Vitals (LCP, FID, CLS) considerations

## Безпека
- XSS захист (sanitization, dangerouslySetInnerHTML аудит)
- CSRF токени для forms
- Secrets не в коді (API keys, tokens, credentials)
- Безпечні dependencies (npm audit, outdated packages)
- Content Security Policy (CSP) headers
- Secure cookies (HttpOnly, Secure, SameSite)

## React Specific (якщо застосовно)
- Proper hooks usage (dependencies arrays, custom hooks)
- Component composition замість inheritance
- Props drilling vs Context API
- Error boundaries implementation
- Key props у lists
- Controlled vs uncontrolled components

## Vue.js Specific (якщо застосовно)
- Composition API vs Options API consistency
- Proper reactivity usage (ref, reactive, computed)
- v-for key bindings
- Event handling patterns
- Slots та props правильність

Приклади використання:
- Review this React component for accessibility and performance
- Check this HTML/CSS for best practices
- Analyze this Vue.js app for security issues
- Audit this SPA for Core Web Vitals optimization
EOF
```

**Перевірка**:
```bash
head -10 ~/.claude/skills/frontend-code-review/SKILL.md
```

Має показати YAML front matter та початок skill опису.

---

### 3.2 TypeScript Checker

```bash
cat > ~/.claude/skills/typescript-checker/SKILL.md << 'EOF'
---
name: typescript-checker
description: Перевіряє TypeScript код на типові помилки, unsafe any, strict режим та покращення tsconfig.
---

# TypeScript Checker Skill

Спеціалізується на глибокому аналізі TypeScript коду та конфігурації:

## Type Safety
- **any types detection**: Виявляє всі `any` типи та пропонує конкретні типи
- **Unknown vs any**: Пропонує `unknown` замість `any` для безпечнішої обробки
- **Union types**: Перевіряє правильність union types (|) та intersection types (&)
- **Generic constraints**: Аналізує generic типи та їх constraints
- **Type guards**: Перевіряє наявність type guards для union types
- **Type predicates**: Використання `is` keyword для type narrowing

## Null Safety
- **strictNullChecks**: Перевірка відповідності strict null checks
- **Optional chaining**: Рекомендації використання `?.` замість manual checks
- **Nullish coalescing**: Використання `??` замість `||` для null/undefined
- **Non-null assertion**: Аудит `!` оператора (часто небезпечний)
- **Undefined vs null**: Consistency перевірка (використовуйте тільки undefined або обидва)

## Function Types
- **Return types**: Явні return types для кращої документації та type safety
- **Function overloads**: Правильність overload signatures
- **Void vs undefined**: Коректне використання void для functions
- **Never type**: Використання never для functions що ніколи не повертаються
- **Async functions**: Return type `Promise<T>` явно вказаний
- **Callback types**: Правильні типи для callbacks та event handlers

## Advanced Types
- **Mapped types**: Використання Partial, Required, Pick, Omit правильно
- **Conditional types**: Type inference з `infer` keyword
- **Template literal types**: String literal types для type-safe strings
- **Utility types**: Readonly, Record, Exclude, Extract, NonNullable
- **Index signatures**: Правильне використання [key: string]: T
- **Branded types**: Nominal typing через branding patterns

## TypeScript Ecosystem
- **@types packages**: Перевірка наявності type definitions для dependencies
- **Declaration files**: .d.ts files правильність
- **Module resolution**: esModuleInterop, allowSyntheticDefaultImports
- **Path aliases**: baseUrl та paths налаштування в tsconfig
- **Triple-slash directives**: /// <reference> коректне використання

## tsconfig.json
- **strict mode**: `strict: true` увімкнено (найвищий рівень безпеки)
- **noImplicitAny**: Заборона implicit any
- **strictNullChecks**: Null safety увімкнено
- **strictFunctionTypes**: Правильна contravariance для function types
- **strictBindCallApply**: Type checking для bind/call/apply
- **noUnusedLocals**: Виявлення unused variables
- **noUnusedParameters**: Виявлення unused function parameters
- **noImplicitReturns**: Всі code paths повинні return value
- **noFallthroughCasesInSwitch**: Switch statements completeness

## Common Pitfalls
- **Type assertions**: `as` keyword overuse (може приховувати bugs)
- **Enum vs const enum**: Performance implications
- **Interface vs Type**: Коли використовувати що
- **Declaration merging**: Небезпеки та best practices
- **Circular dependencies**: Type circular references виявлення

Приклади використання:
- Find and fix all any types in this file
- Check this TypeScript project for type safety issues
- Review tsconfig.json for strict mode compliance
- Analyze these types for better type inference
- Suggest improvements for this complex generic type
EOF
```

---

### 3.3 SEO Analyzer

```bash
cat > ~/.claude/skills/seo-analyzer/SKILL.md << 'EOF'
---
name: seo-analyzer
description: Аналізує HTML сторінки на SEO: мета-теги, заголовки, структуровані дані, технічну SEO та читабельність.
---

# SEO Analyzer Skill

Комплексний SEO аудит для максимальної видимості в пошукових системах:

## Meta Tags (Head Section)
- **Title tag**: Унікальний, описовий, 50-60 символів, містить primary keyword
- **Meta description**: 150-160 символів, compelling CTA, unique per page
- **Meta robots**: index/noindex, follow/nofollow правильність
- **Canonical URL**: Вказує на canonical version для уникнення duplicate content
- **Meta viewport**: mobile-friendly налаштування (width=device-width, initial-scale=1)
- **Meta charset**: UTF-8 encoding для правильного відображення
- **Language meta**: lang attribute на html тезі (наприклад, lang="uk")

## Content Structure
- **H1 tag**: Один H1 на сторінці, унікальний, містить primary keyword
- **H2-H6 hierarchy**: Логічна структура (не пропускати рівні)
- **Paragraph length**: Не занадто довгі (150-300 слів для читабельності)
- **Lists usage**: ul/ol для структурованої інформації
- **Bold/Strong**: Використання для important keywords (не зловживання)
- **Internal links**: 2-5 internal links на сторінці (related content)
- **External links**: Авторитетні джерела, rel="nofollow" для untrusted

## Images SEO
- **Alt text**: Описові alt attributes для всіх images (A11Y + SEO)
- **File names**: Описові назви файлів (not IMG_1234.jpg)
- **Image formats**: WebP для performance, fallback для старих браузерів
- **Lazy loading**: loading="lazy" для below-the-fold images
- **Dimensions**: width та height attributes (CLS prevention)
- **Compression**: Оптимізовані розміри (не 5MB images)

## Structured Data (Schema.org)
- **JSON-LD format**: Preferred над microdata/RDFa
- **Schema types**: Article, Product, Event, Organization, Person (відповідно до контенту)
- **Breadcrumbs**: BreadcrumbList schema для navigation
- **FAQ schema**: FAQPage для Q&A контенту
- **Review schema**: AggregateRating для reviews
- **Validation**: Перевірка в Google Structured Data Testing Tool

## Open Graph (Social Media)
- **og:title**: Facebook/LinkedIn preview title
- **og:description**: Social media description (може відрізнятися від meta description)
- **og:image**: Preview image (1200x630px рекомендовано)
- **og:url**: Canonical URL для sharing
- **og:type**: website/article/product type
- **og:locale**: uk_UA, en_US, etc.

## Twitter Cards
- **twitter:card**: summary/summary_large_image
- **twitter:title**: Twitter-specific title (може відрізнятися)
- **twitter:description**: Twitter description
- **twitter:image**: Twitter preview image
- **twitter:creator**: @username автора

## Technical SEO
- **Mobile-friendly**: Responsive design, no horizontal scroll
- **HTTPS**: Secure connection (Google ranking factor)
- **Page speed**: LCP < 2.5s, FID < 100ms, CLS < 0.1 (Core Web Vitals)
- **Sitemap.xml**: Присутність та правильність
- **Robots.txt**: Не блокує важливі сторінки
- **404 pages**: Custom 404 page з navigation
- **301 redirects**: Permanent redirects для changed URLs
- **URL structure**: Clean URLs (not /page?id=123, use /page/name)
- **HTTPS redirects**: HTTP→HTTPS redirects налаштовані

## Content Quality
- **Keyword density**: 1-2% для primary keyword (не spam)
- **LSI keywords**: Related keywords присутні
- **Readability**: Flesch-Kincaid score 60+ (8th grade level)
- **Content length**: 1000+ слів для blog posts (але якість > кількість)
- **Uniqueness**: Не дублікат контенту з інших сторінок
- **Freshness**: Дата публікації та оновлення (для news/blogs)

## Multilingual SEO (якщо застосовно)
- **hreflang tags**: <link rel="alternate" hreflang="uk" href="...">
- **Language switcher**: User-friendly мовний switcher
- **Translated URLs**: /uk/, /en/, /de/ structure
- **Content consistency**: Повний переклад, не machine translation

## Local SEO (якщо застосовно)
- **NAP consistency**: Name, Address, Phone number однакові всюди
- **Google My Business**: Schema для LocalBusiness
- **Local keywords**: Місто/регіон в контенті
- **Reviews**: Schema для reviews з location

Приклади використання:
- Analyze this HTML page for SEO issues and improvements
- Review meta tags for this landing page
- Check structured data implementation for e-commerce product
- Audit multilingual site for hreflang correctness
- Evaluate Core Web Vitals impact on SEO
EOF
```

---

### 3.4 Tailwind Validator

```bash
cat > ~/.claude/skills/tailwind-validator/SKILL.md << 'EOF'
---
name: tailwind-validator
description: Перевіряє використання Tailwind CSS: валідність класів, організацію, responsive breakpoints, dark mode та оптимізацію.
---

# Tailwind Validator Skill

Спеціалізований аналіз Tailwind CSS використання:

## Class Validity
- **Existing classes only**: Перевірка що всі класи існують в Tailwind (не typos)
- **Deprecated classes**: Виявлення застарілих класів (наприклад, `flex-grow-0` → `grow-0`)
- **Custom classes**: Відповідність tailwind.config.js (якщо кастомні класи)
- **Plugin classes**: Перевірка що classes з plugins (@tailwindcss/forms) доступні
- **JIT mode**: Arbitrary values валідація (наприклад, `w-[147px]`)

## Class Organization
- **Redundant classes**: Дублікати (наприклад, `p-4 padding-4`)
- **Conflicting classes**: Класи що перезаписують один одного (наприклад, `text-sm text-lg`)
- **Grouping**: Логічне групування (layout → typography → colors → spacing)
- **Order consistency**: Однаковий порядок класів в проекті
- **Utility-first**: Переважно utilities замість custom CSS

## Responsive Design
- **Breakpoints usage**: sm (640px), md (768px), lg (1024px), xl (1280px), 2xl (1536px)
- **Mobile-first approach**: Base styles для mobile, потім md:, lg: для більших екранів
- **Container usage**: container class для responsive width
- **Max-width**: Правильне використання max-w-* utilities
- **Hidden/visible**: Responsive visibility (hidden md:block)

## Layout Patterns
- **Flexbox**: flex, flex-row, flex-col, justify-*, items-*, gap-*
- **Grid**: grid, grid-cols-*, gap-*, place-items-*
- **Spacing**: p-*, m-*, space-x-*, space-y-* правильність
- **Positioning**: relative, absolute, fixed, sticky з координатами (top-*, left-*)
- **Z-index**: z-* utilities для layering

## Typography
- **Font sizes**: text-xs to text-9xl правильне використання
- **Font weights**: font-thin to font-black
- **Line height**: leading-* для readability
- **Letter spacing**: tracking-* usage
- **Text colors**: text-* з color palette
- **Text alignment**: text-left/center/right/justify

## Colors & Theming
- **Color palette**: Використання default palette (slate, gray, red, etc.)
- **Custom colors**: tailwind.config.js theme.colors consistency
- **Opacity**: bg-blue-500/50 syntax для opacity
- **Gradients**: bg-gradient-to-* з from-*/via-*/to-*
- **Dark mode**: dark: prefix правильність

## States & Variants
- **Hover**: hover:* для interactive елементів
- **Focus**: focus:ring-*, focus:outline-* для A11Y
- **Active**: active:* для buttons/links
- **Disabled**: disabled:opacity-50 etc.
- **Group**: group-hover:* для nested hovers
- **Peer**: peer-checked:* для sibling state

## Dark Mode
- **Class strategy**: class dark mode (не media query) в config
- **dark: prefix**: Використання на всіх color utilities
- **Consistency**: Всі bg-*/text-* мають dark: variants
- **Toggle implementation**: Dark mode toggle functionality

## Arbitrary Values (JIT)
- **Syntax**: Правильні квадратні дужки [value]
- **Valid CSS values**: w-[147px], top-[117px], text-[#bada55]
- **When to use**: Тільки для one-off values (не замість theme extend)
- **Performance**: Не зловживання (краще extend theme)

## tailwind.config.js
- **Content paths**: Правильні paths для purging (./src/**/*.{js,jsx,ts,tsx})
- **Theme extend**: Custom values в theme.extend (не перезаписувати theme)
- **Plugins**: @tailwindcss/forms, @tailwindcss/typography, @tailwindcss/aspect-ratio
- **SafeLIST**: safelist для dynamic classes (якщо потрібно)
- **Prefix**: Використання prefix (якщо конфлікти з іншими CSS)

## Bundle Optimization
- **Unused classes**: Потенційні unused utilities (з unused CSS)
- **PurgeCSS**: Правильна конфігурація content paths
- **JIT mode**: Увімкнення JIT для on-demand utilities
- **Production build**: NODE_ENV=production для minification
- **File size**: Final CSS розмір (<100KB після gzip ідеально)

## Accessibility with Tailwind
- **Focus rings**: focus:ring-2 focus:ring-offset-2 для keyboard nav
- **Screen reader only**: sr-only utility для invisible but accessible content
- **Contrast**: Достатній контраст між text/bg colors (WCAG AA)

## Common Anti-patterns
- **Inline styles**: Не використовувати style={{}} якщо є Tailwind utility
- **!important**: Уникати arbitrary values з ! (наприклад, !w-full)
- **Too many classes**: Якщо >15 класів, розгляньте @apply у CSS або component
- **Magic numbers**: w-[147px] без пояснення (краще semantic named value)

Приклади використання:
- Review this component for Tailwind CSS best practices
- Optimize these Tailwind classNames for mobile-first design
- Validate tailwind.config.js setup and suggest improvements
- Check dark mode implementation across this codebase
- Audit responsive breakpoints usage
EOF
```

---

### 3.5 Cloudflare Inspector

```bash
cat > ~/.claude/skills/cloudflare-inspector/SKILL.md << 'EOF'
---
name: cloudflare-inspector
description: Аналізує Cloudflare конфігурацію: DNS, кешування, SSL/TLS, WAF, Rules та Workers для продуктивності й безпеки.
---

# Cloudflare Inspector Skill

Комплексний аудит Cloudflare інфраструктури:

## DNS Configuration
- **A records**: IPv4 addresses правильність, proxied (orange cloud) vs DNS-only (grey cloud)
- **AAAA records**: IPv6 addresses (рекомендовано для modern sites)
- **CNAME records**: Aliases, CNAME flattening для root domain
- **MX records**: Email routing, priority values
- **TXT records**: SPF, DKIM, DMARC для email authentication, domain verification
- **TTL settings**: 300s (5min) для dynamic, 86400s (24h) для static
- **DNSSEC**: Увімкнено для додаткової безпеки (prevents DNS spoofing)
- **CAA records**: Certificate Authority Authorization (які CA можуть видавати certificates)

## Caching Strategy
- **Cache Level**: Standard (cache static), Ignore Query String, Cache Everything
- **Browser Cache TTL**: 4 hours to 1 year (залежно від content type)
- **Edge Cache TTL**: Cloudflare's cache expiration (може відрізнятися від Browser TTL)
- **Cache Everything**: Page Rule для caching HTML (обережно з dynamic content)
- **Bypass Cache**: Page Rule для admin panels, API endpoints
- **Cache Keys**: Custom Cache Keys для query parameters handling
- **Tiered Caching**: Увімкнення для кращого hit rate

## SSL/TLS Configuration
- **SSL Mode**:
  - ❌ Off - Незахищено (NEVER use)
  - ⚠️ Flexible - Cloudflare→Origin HTTP (vulnerable to MITM)
  - ✅ Full - Cloudflare→Origin HTTPS (але self-signed OK)
  - ✅✅ Full (Strict) - Cloudflare→Origin HTTPS з valid certificate (РЕКОМЕНДОВАНО)
- **Edge Certificates**: Auto-renewal, validity period
- **Always Use HTTPS**: Redirect HTTP→HTTPS (MUST have)
- **HSTS**: HTTP Strict Transport Security (max-age=31536000, includeSubDomains, preload)
- **Minimum TLS Version**: TLS 1.2+ (TLS 1.0/1.1 deprecated)
- **TLS 1.3**: Увімкнено для кращої performance
- **Opportunistic Encryption**: Увімкнено
- **Certificate Transparency**: Monitoring для certificate issuance

## Security (WAF & Firewall)
- **Web Application Firewall**: Managed Rulesets увімкнено
- **OWASP Core Ruleset**: Protection від SQL injection, XSS, etc.
- **Cloudflare Managed Ruleset**: Automatically updated rules
- **DDoS Protection**: Automatic (завжди увімкнено на всіх планах)
- **Bot Fight Mode**: Challenge suspected bots (Free plan) / Super Bot Fight Mode (paid)
- **Security Level**: Medium (recommended) / High (для sensitive sites)
- **Challenge Passage**: 30 minutes default
- **Browser Integrity Check**: Увімкнено (blocks headless browsers)
- **Rate Limiting**: Custom rules для API endpoints (наприклад, 100 requests/minute)

## Page Rules (Legacy)
- **Limit**: 3 rules (Free), 20 (Pro), 50 (Business), 125 (Enterprise)
- **Priority**: Order matters (top to bottom execution)
- **Common patterns**:
  - `example.com/admin/*` → Security Level: High, Disable Apps
  - `example.com/api/*` → Cache Level: Bypass
  - `example.com/static/*` → Cache Level: Cache Everything, Edge TTL: 1 year
- **Wildcards**: `*` matches zero or more characters
- **Overlaps**: Avoid overlapping rules (confusing behavior)

## Redirect Rules (New)
- **301 Permanent**: For moved content (SEO juice transfer)
- **302 Temporary**: For temporary changes
- **URL patterns**: Wildcard matching (`/old-page/*` → `/new-page/*`)
- **Preserve query string**: Important for tracking parameters
- **HTTPS redirects**: HTTP→HTTPS (automatic if "Always Use HTTPS" enabled)

## Transform Rules
- **URL Rewrite**: Internal rewrites (user sees A, server gets B)
- **Header Modification**: Add/Remove/Override HTTP headers
- **Common uses**:
  - Add security headers (CSP, X-Frame-Options)
  - Remove server headers (hide backend tech)
  - Rewrite URLs for clean routing

## Cloudflare Workers
- **Routes**: Pattern matching правильність (`example.com/api/*`)
- **Environment variables**: Secrets management (не хардкодити в Worker)
- **Error handling**: try/catch blocks у fetch handlers
- **Response headers**: CORS, CSP, caching headers
- **Performance**: CPU time limits (10ms Free, 50ms paid per request)
- **Logging**: console.log() для debugging (доступно в dashboard)
- **KV Storage**: Key-value storage для state (TTL налаштування)
- **Durable Objects**: Stateful coordination (для WebSockets, etc.)

## Workers Common Issues
- **Missing error handling**:
  ```js
  // BAD
  addEventListener('fetch', event => {
    event.respondWith(fetch(event.request));
  });

  // GOOD
  addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request).catch(err =>
      new Response('Error: ' + err.message, { status: 500 })
    ));
  });
  ```
- **CORS issues**: Missing Access-Control-Allow-Origin headers
- **Caching**: Правильне використання Cache API
- **Secrets in code**: Use environment variables, not hardcoded API keys
- **Infinite loops**: Worker calling itself (avoid with proper routing)

## Performance Optimization
- **Auto Minify**: HTML/CSS/JavaScript minification (Free!)
- **Brotli Compression**: Кращий за gzip (automatic)
- **HTTP/2**: Multiplexing (automatic)
- **HTTP/3 (QUIC)**: Faster connection establishment (увімкнути)
- **Rocket Loader**: Async JavaScript loading (обережно, може break деякі scripts)
- **Polish**: Image optimization (lossy/lossless) (paid feature)
- **Mirage**: Image lazy-loading для mobile (paid)
- **Argo Smart Routing**: Faster routing через Cloudflare network (paid)

## Analytics & Monitoring
- **Web Analytics**: Privacy-first analytics (без cookies)
- **Cache Analytics**: Hit rate, bandwidth saved
- **Security Events**: WAF blocks, challenges issued
- **Workers Analytics**: Requests, errors, CPU time
- **Real User Monitoring (RUM)**: Core Web Vitals tracking

## Common Misconfigurations
- **SSL Mode Flexible**: ⚠️ Vulnerable to MITM attacks → Use Full (Strict)
- **Cache Everything без Bypass**: Caching login pages → Add Page Rule to bypass
- **No Rate Limiting**: API abuse → Add Rate Limiting rules
- **Development Mode забули вимкнути**: Bypasses cache → Вимкнути після testing
- **Wildcard SSL not enabled**: Subdomains not covered → Enable Universal SSL
- **HSTS без testing**: Можна lock out site → Test з малим max-age спочатку

Приклади використання:
- Review my Cloudflare DNS and SSL configuration for security issues
- Analyze this Cloudflare Worker script for performance and error handling
- Audit WAF and security settings for e-commerce site
- Check caching strategy for optimal performance
- Validate Page Rules and Redirect Rules setup
EOF
```

---

## Етап 4: Перезавантаження Claude CLI

### 4.1 Вихід з поточної сесії

```bash
exit
```

### 4.2 Запуск Claude CLI

```bash
claude
```

### 4.3 Перевірка skills

У Claude CLI виконайте:

```
What Skills are available?
```

**Очікуваний результат**: список має містити всі 5 skills:
- frontend-code-review
- typescript-checker
- seo-analyzer
- tailwind-validator
- cloudflare-inspector

---

## Етап 5: Тестування skills

### 5.1 Тест Frontend Code Review

```
Review this React component for accessibility:

const Button = ({ onClick }) => (
  <div onClick={onClick}>Click me</div>
);
```

**Очікується**: skill має знайти проблеми з семантикою (div замість button), відсутність keyboard navigation, accessibility issues.

---

### 5.2 Тест TypeScript Checker

```
Find type issues:

function getData(): any {
  return fetch('/api');
}
```

**Очікується**: skill має запропонувати замінити `any` на `Promise<Response>`.

---

### 5.3 Тест SEO Analyzer

```
Analyze this HTML for SEO:

<html>
  <head><title></title></head>
  <body><p>Content</p></body>
</html>
```

**Очікується**: skill має знайти відсутні meta description, H1, structured data, etc.

---

### 5.4 Тест Tailwind Validator

```
Review these Tailwind classes:

<div className="flex flex-row p-4 padding-4 text-sm text-lg">
```

**Очікується**: skill має знайти redundant `flex-row`, invalid `padding-4`, conflicting `text-sm text-lg`.

---

### 5.5 Тест Cloudflare Inspector

```
Review this Cloudflare Worker:

addEventListener('fetch', event => {
  event.respondWith(fetch(event.request));
});
```

**Очікується**: skill має запропонувати додати error handling, CORS headers, logging.

---

## Troubleshooting

### Проблема: Skills не відображаються

```bash
# 1. Перевірити файли
ls -la ~/.claude/skills/*/SKILL.md

# 2. Перевірити формат першого skill
head -10 ~/.claude/skills/frontend-code-review/SKILL.md

# 3. Перевірити права доступу
chmod -R 644 ~/.claude/skills/*/SKILL.md
chmod -R 755 ~/.claude/skills/*/

# 4. Повторити перезапуск
exit
claude
```

---

### Проблема: Skill показує помилку

```bash
# Перевірити YAML front matter синтаксис
cat ~/.claude/skills/frontend-code-review/SKILL.md | head -5

# Має бути ТОЧНО:
# ---
# name: frontend-code-review
# description: ...
# ---
```

**Типові помилки**:
- Відсутні `---` на початку/кінці
- Пропущено `name:` або `description:`
- Зайві пробіли перед `name:`
- Не закритий YAML block (другі `---`)

---

### Проблема: Skill conflicts з вбудованими

Якщо вбудовані skills `frontend-code-review` вже існують:

1. **Перейменуйте кастомні**:
   ```bash
   mv ~/.claude/skills/frontend-code-review ~/.claude/skills/frontend-review-extended
   # У SKILL.md змініть name: frontend-review-extended
   ```

2. **Або видаліть вбудовані** (якщо впевнені):
   ```bash
   # Backup спочатку
   cp -r ~/.claude/skills ~/.claude/skills.builtin.backup
   # Потім встановіть кастомні
   ```

---

## Підсумок

Після завершення всіх етапів у вас має бути:

- ✅ 5 skills у `~/.claude/skills/`
- ✅ Кожен skill з валідним SKILL.md файлом
- ✅ Claude CLI показує всі skills у списку
- ✅ Skills працюють при тестуванні

**Наступні кроки**:
- Використовуйте skills у вашому workflow
- Додавайте власні приклади та покращення
- Створюйте нові skills за потребою

**Документація**:
- Детальні приклади: `.claude/skills-installer/QUICK_REFERENCE.md`
- Чекліст: `.claude/skills-installer/claude_skills_checklist.md`
- Опис файлів: `.claude/skills-installer/FILES_OVERVIEW.md`
