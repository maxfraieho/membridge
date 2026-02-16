# Claude Skills Installation Checklist

Використовуйте цей checklist для валідації після встановлення skills.

---

## Pre-Installation

- [ ] Claude CLI встановлено (`claude --version` працює)
- [ ] Директорія `~/.claude/` існує
- [ ] Backup існуючих skills (якщо є): `cp -r ~/.claude/skills ~/.claude/skills.backup`

---

## Option A: Global Installation (~/.claude/skills/)

### Installation Steps

- [ ] Скрипт запущено: `bash .claude/skills-installer/claude_skills_auto_install.sh`
- [ ] Скрипт завершився без помилок
- [ ] Всі 5 skills показано у виводі скрипта (✓ checkmarks)

### File Verification

- [ ] `~/.claude/skills/frontend-code-review/SKILL.md` існує
- [ ] `~/.claude/skills/typescript-checker/SKILL.md` існує
- [ ] `~/.claude/skills/seo-analyzer/SKILL.md` існує
- [ ] `~/.claude/skills/tailwind-validator/SKILL.md` існує
- [ ] `~/.claude/skills/cloudflare-inspector/SKILL.md` існує

### YAML Front Matter Check

Для кожного SKILL.md файлу перевірте:

#### frontend-code-review
- [ ] Починається з `---`
- [ ] Є рядок `name: frontend-code-review`
- [ ] Є рядок `description: ...` (не порожній)
- [ ] Закінчується front matter з `---`
- [ ] Після `---` є markdown контент

#### typescript-checker
- [ ] Починається з `---`
- [ ] Є `name: typescript-checker`
- [ ] Є `description: ...`
- [ ] Правильний YAML format

#### seo-analyzer
- [ ] Починається з `---`
- [ ] Є `name: seo-analyzer`
- [ ] Є `description: ...`
- [ ] Правильний YAML format

#### tailwind-validator
- [ ] Починається з `---`
- [ ] Є `name: tailwind-validator`
- [ ] Є `description: ...`
- [ ] Правильний YAML format

#### cloudflare-inspector
- [ ] Починається з `---`
- [ ] Є `name: cloudflare-inspector`
- [ ] Є `description: ...`
- [ ] Правильний YAML format

---

## Option C: Project-Local Installation (.claude/skills/)

### Installation Steps

- [ ] Директорія `.claude/skills/` створена в проекті
- [ ] Всі 5 skills скопійовано до `.claude/skills/`
- [ ] Файли мають правильну структуру

### File Verification

- [ ] `.claude/skills/frontend-code-review/SKILL.md` існує
- [ ] `.claude/skills/typescript-checker/SKILL.md` існує
- [ ] `.claude/skills/seo-analyzer/SKILL.md` існує
- [ ] `.claude/skills/tailwind-validator/SKILL.md` існує
- [ ] `.claude/skills/cloudflare-inspector/SKILL.md` існує

### .gitignore Check

- [ ] `.claude/skills/` додано до `.gitignore` (якщо не хочете commitити)
- [ ] АБО skills закоммічено до git (якщо хочете share з командою)

---

## Post-Installation Validation

### Claude CLI Restart

- [ ] Вийшли з Claude CLI: `exit`
- [ ] Запустили знову: `claude`
- [ ] Claude CLI завантажився без помилок

### Skills Availability Check

У Claude CLI виконайте:

```
What Skills are available?
```

**Перевірте наявність**:
- [ ] `frontend-code-review` у списку
- [ ] `typescript-checker` у списку
- [ ] `seo-analyzer` у списку
- [ ] `tailwind-validator` у списку
- [ ] `cloudflare-inspector` у списку

**Якщо skills не відображаються**: перевірте секцію Troubleshooting нижче.

---

## Functional Testing

### 1. Frontend Code Review Test

```
Review this React component for accessibility:

const Button = ({ onClick }) => (
  <div onClick={onClick}>Click me</div>
);
```

**Перевірте відповідь**:
- [ ] Claude використав skill `frontend-code-review`
- [ ] Знайдено проблему з семантикою (div замість button)
- [ ] Згадано про keyboard accessibility
- [ ] Запропоновано виправлення

---

### 2. TypeScript Checker Test

```
Find type issues:

function getData(): any {
  return fetch('/api');
}
```

**Перевірте відповідь**:
- [ ] Claude використав skill `typescript-checker`
- [ ] Виявлено `any` type
- [ ] Запропоновано конкретний тип (Promise<Response>)
- [ ] Згадано про type safety

---

### 3. SEO Analyzer Test

```
Analyze this HTML for SEO:

<html>
  <head><title></title></head>
  <body><p>Content</p></body>
</html>
```

**Перевірте відповідь**:
- [ ] Claude використав skill `seo-analyzer`
- [ ] Знайдено відсутню meta description
- [ ] Знайдено порожній title
- [ ] Знайдено відсутність H1
- [ ] Запропоновано structured data

---

### 4. Tailwind Validator Test

```
Review these Tailwind classes:

<div className="flex flex-row p-4 padding-4 text-sm text-lg invalid-class">
```

**Перевірте відповідь**:
- [ ] Claude використав skill `tailwind-validator`
- [ ] Знайдено redundant `flex-row`
- [ ] Знайдено invalid `padding-4`
- [ ] Знайдено conflicting `text-sm` та `text-lg`
- [ ] Знайдено `invalid-class` (не існує в Tailwind)

---

### 5. Cloudflare Inspector Test

```
Review this Cloudflare Worker:

addEventListener('fetch', event => {
  event.respondWith(fetch(event.request));
});
```

**Перевірте відповідь**:
- [ ] Claude використав skill `cloudflare-inspector`
- [ ] Знайдено відсутність error handling
- [ ] Запропоновано додати try/catch
- [ ] Згадано про CORS headers (можливо)
- [ ] Запропоновано logging для debugging

---

## Troubleshooting

### Problem: Skills не відображаються

**Діагностика**:

```bash
# 1. Перевірити чи файли існують
ls -la ~/.claude/skills/*/SKILL.md

# 2. Перевірити перший skill детально
cat ~/.claude/skills/frontend-code-review/SKILL.md | head -10
```

**Якщо файли не існують**:
- [ ] Повторити installation скрипт
- [ ] Перевірити чи скрипт завершився без помилок

**Якщо файли існують але skills не показуються**:
- [ ] Перевірити YAML front matter синтаксис (має бути --- на початку і кінці)
- [ ] Перевірити чи немає зайвих пробілів перед `name:` та `description:`
- [ ] Перезапустити Claude CLI (`exit` потім `claude`)

---

### Problem: YAML Parse Error

**Симптоми**: Помилка при завантаженні skills

**Перевірте**:

```bash
# Показати перші 5 рядків SKILL.md
head -5 ~/.claude/skills/frontend-code-review/SKILL.md
```

**Має бути ТОЧНО**:
```
---
name: frontend-code-review
description: Проводить детальний review frontend коду...
---

```

**Типові помилки**:
- [ ] Відсутні `---` на початку
- [ ] Відсутні `---` після description
- [ ] Пробіли перед `name:` або `description:`
- [ ] Використання табуляції замість пробілів
- [ ] Лапки в description не екрануються

**Виправлення**:
```bash
# Відкрити файл для редагування
nano ~/.claude/skills/frontend-code-review/SKILL.md

# Переконатися що front matter правильний
```

---

### Problem: Skill conflicts з вбудованими

**Симптоми**: Claude каже що skill вже існує або показує неочікувану поведінку

**Діагностика**:

User skills (`.claude/skills/`) мають **пріоритет** над вбудованими. Це означає що ваші кастомні skills перезапишуть built-in.

**Опції**:

1. **Перейменувати кастомні skills**:
   ```bash
   # Приклад: frontend-code-review → frontend-review-extended
   mv ~/.claude/skills/frontend-code-review ~/.claude/skills/frontend-review-extended

   # Відкрити SKILL.md та змінити name:
   nano ~/.claude/skills/frontend-review-extended/SKILL.md
   # Змінити: name: frontend-review-extended
   ```

2. **Використовувати project-local skills** (Option C):
   - Встановити skills у `.claude/skills/` (в проекті, не global)
   - Claude буде використовувати project skills тільки для цього проекту

3. **Видалити вбудовані** (не рекомендується):
   ```bash
   # Спочатку backup
   cp -r ~/.claude/skills ~/.claude/skills.builtin.backup
   # Потім видалити конфліктуючі
   ```

---

### Problem: Permission Denied

**Симптоми**: `bash: Permission denied: claude_skills_auto_install.sh`

**Виправлення**:

```bash
# Додати execution права
chmod +x .claude/skills-installer/claude_skills_auto_install.sh

# Потім запустити
bash .claude/skills-installer/claude_skills_auto_install.sh
```

---

### Problem: Skills працюють але дають неправильні відповіді

**Діагностика**:

Це може бути через:
1. Skill description надто загальний (Claude не розуміє коли використовувати)
2. Skill content надто короткий (недостатньо контексту)
3. Конфлікт з іншими skills

**Виправлення**:

```bash
# 1. Перевірити довжину skill файлу
wc -l ~/.claude/skills/frontend-code-review/SKILL.md
# Має бути 100+ рядків для детального skill

# 2. Прочитати skill content
less ~/.claude/skills/frontend-code-review/SKILL.md

# 3. Порівняти з еталонним (якщо маєте)
diff ~/.claude/skills/frontend-code-review/SKILL.md .claude/skills-installer/reference/frontend-code-review.md
```

---

## Final Checklist Summary

**Після завершення всіх перевірок**:

- [ ] ✅ Всі 5 skills встановлено
- [ ] ✅ Claude CLI показує skills у списку
- [ ] ✅ Functional tests пройдено для всіх 5 skills
- [ ] ✅ Немає помилок або warnings
- [ ] ✅ Skills працюють правильно (дають релевантні відповіді)

**Якщо всі checkboxes позначені**: 🎉 **Installation успішна!**

**Якщо є проблеми**: перегляньте Troubleshooting секцію або:
1. Створіть issue в репозиторії проекту
2. Перегляньте детальну документацію: `.claude/skills-installer/README.md`
3. Спробуйте ручну установку: `.claude/skills-installer/claude_skills_setup_prompt.md`

---

## Next Steps

1. **Використовуйте skills у production**:
   - Frontend code review перед PR merge
   - TypeScript checking при рефакторингу
   - SEO analysis для нових landing pages
   - Tailwind validation при створенні components
   - Cloudflare audit після config changes

2. **Додайте власні приклади**:
   - Створіть `.claude/skills-installer/examples/` з реальними use cases
   - Документуйте успішні випадки використання

3. **Розширте skills**:
   - Додайте нові перевірки до існуючих SKILL.md
   - Створіть нові skills для специфічних потреб проекту

4. **Share з командою**:
   - Закоммітьте `.claude/skills-installer/` до git
   - Додайте інструкції в team README
   - Проведіть demo session

**Happy coding with Claude Skills! 🚀**
