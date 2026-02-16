# Claude Skills - Master Installation Guide

Цей гайд описує **3 варіанти** встановлення Claude CLI skills для проекту `violin.pp.ua`.

---

## 🎯 Огляд варіантів

| Варіант | Розташування | Область дії | Git | Рекомендовано для |
|---------|--------------|-------------|-----|-------------------|
| **A: Global** | `~/.claude/skills/` | Всі проекти | ❌ Ні | Персональні налаштування |
| **B: Quick Test** | `~/.claude/skills/` | Всі проекти | ❌ Ні | Швидке тестування |
| **C: Project-Local** | `.claude/skills-local/` | Тільки цей проект | ✅ Так | **Production use** ⭐ |

---

## 📦 Option A: Global Installation

**Призначення**: Встановити skills глобально для використання в усіх проектах.

### Переваги
- ✅ Одна установка для всіх проектів
- ✅ Не потрібно встановлювати в кожному проекті
- ✅ Легше оновлювати (один раз для всього)

### Недоліки
- ❌ Не версійно контролюється (не в Git)
- ❌ Можливі конфлікти між проектами
- ❌ Важче синхронізувати в команді

### Установка

```bash
# 1. Запустити автоматичний інсталятор
bash .claude/skills-installer/claude_skills_auto_install.sh

# 2. Перезапустити Claude CLI
exit
claude

# 3. Перевірити
What Skills are available?
```

### Очікуваний результат

```
~/.claude/skills/
├── frontend-code-review/SKILL.md
├── typescript-checker/SKILL.md
├── seo-analyzer/SKILL.md
├── tailwind-validator/SKILL.md
└── cloudflare-inspector/SKILL.md
```

**Кількість skills**: 5 нових + існуючі глобальні

---

## ⚡ Option B: Quick Test Installation

**Призначення**: Швидка установка з мінімальними описами для тестування.

### Переваги
- ✅ Дуже швидко (~5 секунд)
- ✅ Менший розмір файлів
- ✅ Ідеально для demo

### Недоліки
- ❌ Коротші описи в SKILL.md (менше контексту)
- ❌ Не в Git (як Option A)
- ❌ Може бути недостатньо для складних випадків

### Установка

```bash
# 1. Запустити швидкий інсталятор
bash .claude/skills-installer/quick_install.sh

# 2. Перезапустити Claude CLI
exit
claude
```

### Використання

Для quick testing та demo, коли не потрібні детальні описи.

---

## 🏆 Option C: Project-Local Installation (RECOMMENDED)

**Призначення**: Ізольовані project-specific skills з версійним контролем.

### Переваги
- ✅ **Version control** (можна commitити до Git)
- ✅ **Isolation** (немає конфліктів з іншими проектами)
- ✅ **Team sharing** (вся команда має однакові skills)
- ✅ **Dual-path** (локальні + глобальні skills одночасно)
- ✅ **Production-ready** (стабільна конфігурація)

### Недоліки
- ⚠️ Потрібно встановити в кожному проекті (але це один раз)
- ⚠️ Більше дискового простору (але ~500KB на проект)

### Установка (Автоматична)

**Поточний проект вже налаштовано! ✅**

Структура вже створена:

```
.claude/skills-local/
├── frontend-code-review/SKILL.md
├── typescript-checker/SKILL.md
├── seo-analyzer/SKILL.md
├── tailwind-validator/SKILL.md
└── cloudflare-inspector/SKILL.md

.claude/skills-project → symlink to skills-local/

~/.config/claude/config.json:
{
  "skills_path": [
    "/home/vokov/.../violin.pp.ua/.claude/skills-local",
    "/root/.claude/skills"
  ]
}
```

### Встановлення в інших проектах

Якщо хочете використати цю структуру в інших проектах:

```bash
# 1. Скопіювати skills-local до нового проекту
cp -r /path/to/violin.pp.ua/.claude/skills-local /path/to/new-project/.claude/

# 2. Створити symlink
cd /path/to/new-project
ln -sf "$(pwd)/.claude/skills-local" .claude/skills-project

# 3. Оновити config.json
CONFIG_FILE="$HOME/.config/claude/config.json"
NEW_PROJECT_PATH="$(pwd)/.claude/skills-local"

# Додати новий шлях до skills_path (якщо ще немає)
jq --arg path "$NEW_PROJECT_PATH" '.skills_path += [$path] | .skills_path |= unique' "$CONFIG_FILE" > tmp.json && mv tmp.json "$CONFIG_FILE"

# 4. Перевірити
cat "$CONFIG_FILE" | jq '.skills_path'
```

### Верифікація

```bash
# Перевірити структуру
ls -la .claude/skills-local/

# Перевірити SKILL.md файли
for skill in .claude/skills-local/*/SKILL.md; do
  echo "$(basename $(dirname $skill)): $(wc -l < $skill) lines"
done

# Перевірити symlink
readlink .claude/skills-project

# Перевірити config
jq '.skills_path' ~/.config/claude/config.json
```

**Очікуваний результат**:
- 5 directories в `.claude/skills-local/`
- 5 SKILL.md файлів (кожен ~20-50 рядків)
- Symlink pointing to correct path
- Config містить обидва шляхи (local + global)

---

## 🔄 Comparison Matrix

| Feature | Option A (Global) | Option B (Quick) | Option C (Local) |
|---------|-------------------|------------------|------------------|
| Installation time | 10s | 5s | 15s |
| Disk space | ~500KB | ~200KB | ~500KB per project |
| Git control | ❌ | ❌ | ✅ |
| Team sharing | ❌ | ❌ | ✅ |
| Conflict isolation | ❌ | ❌ | ✅ |
| Global + local skills | ❌ | ❌ | ✅ (dual-path) |
| Skill detail level | Full | Minimal | Full |
| Production use | ⚠️ | ❌ | ✅ |
| Easy updates | ✅ | ✅ | ⚠️ (per project) |

---

## 📋 Post-Installation Checklist

Незалежно від обраного варіанту:

- [ ] Skills files створено
- [ ] YAML front matter валідний (--- на початку/кінці)
- [ ] Claude CLI перезапущено (`exit` → `claude`)
- [ ] `What Skills are available?` показує нові skills
- [ ] Functional test пройдено (1+ skill test)

### Quick Functional Test

```
# В Claude CLI виконайте:
Review this for Tailwind issues:

<div className="flex flex-row p-4 padding-4 text-sm text-lg">
```

**Очікується**: Claude має використати `tailwind-validator` skill і знайти:
- `flex-row` redundant
- `padding-4` invalid
- `text-sm` conflicts with `text-lg`

---

## 🛠️ Maintenance

### Оновлення skills

**Option A/B (Global)**:
```bash
bash .claude/skills-installer/claude_skills_auto_install.sh
# Перезаписує існуючі файли
```

**Option C (Local)**:
```bash
# 1. Backup існуючих
cp -r .claude/skills-local .claude/skills-local.backup.$(date +%Y%m%d)

# 2. Оновити файли (вручну або скриптом)
# Наприклад, додати нові перевірки до SKILL.md

# 3. Git commit
git add .claude/skills-local/
git commit -m "feat: update project skills with new checks"
```

### Backup

```bash
# Global
cp -r ~/.claude/skills ~/.claude/skills.backup.$(date +%Y%m%d)

# Local
cp -r .claude/skills-local .claude/skills-local.backup.$(date +%Y%m%d)
```

### Rollback

```bash
# Global
mv ~/.claude/skills.backup.YYYYMMDD ~/.claude/skills

# Local
mv .claude/skills-local.backup.YYYYMMDD .claude/skills-local
```

---

## 🐛 Troubleshooting

### Skills не показуються

**Problem**: `What Skills are available?` не показує нові skills

**Solution**:
1. Перевірити файли існують:
   ```bash
   ls -la ~/.claude/skills/*/SKILL.md  # Global
   ls -la .claude/skills-local/*/SKILL.md  # Local
   ```

2. Перевірити YAML format:
   ```bash
   head -5 ~/.claude/skills/frontend-code-review/SKILL.md
   # Має бути:
   # ---
   # name: frontend-code-review
   # description: ...
   # ---
   ```

3. Перезапустити Claude CLI:
   ```bash
   exit
   claude
   ```

4. Якщо Option C, перевірити config:
   ```bash
   jq '.skills_path' ~/.config/claude/config.json
   ```

### Config.json не оновлюється

**Problem**: `jq` команда не працює

**Solution**:
```bash
# Встановити jq
apk add jq  # Alpine
apt install jq  # Debian/Ubuntu

# Або вручну редагувати
nano ~/.config/claude/config.json
# Додати:
# "skills_path": [
#   "/path/to/project/.claude/skills-local",
#   "/root/.claude/skills"
# ]
```

### Symlink не працює

**Problem**: `.claude/skills-project` не вказує на правильну директорію

**Solution**:
```bash
# Видалити старий symlink
rm .claude/skills-project

# Створити новий з абсолютним шляхом
ln -sf "$(pwd)/.claude/skills-local" .claude/skills-project

# Перевірити
readlink .claude/skills-project
```

---

## 📚 Related Files

- **README.md** - Детальна документація skills
- **claude_skills_setup_prompt.md** - Покрокова ручна установка
- **claude_skills_checklist.md** - Validation checklist
- **QUICK_REFERENCE.md** - Щоденна шпаргалка
- **skills_manifest.json** - Machine-readable опис
- **FILES_OVERVIEW.md** - Опис всіх файлів

---

## 🎓 Recommendations

**Для індивідуальних розробників**:
- Використовуйте **Option A** (Global) якщо працюєте тільки над одним проектом
- Використовуйте **Option C** (Local) якщо працюєте над багатьма проектами з різними skills

**Для команд**:
- **ЗАВЖДИ Option C** (Local) для консистентності в команді
- Commitьте `.claude/skills-local/` до Git
- Додайте setup instructions до project README

**Для тестування**:
- **Option B** (Quick) для швидкого demo
- Потім мігруйте на Option A або C для production

---

## ✅ Success Criteria

**Ви успішно встановили skills коли**:

1. ✅ `What Skills are available?` показує всі 5 нових skills
2. ✅ Functional test працює (Claude використовує skills)
3. ✅ Немає помилок при завантаженні Claude CLI
4. ✅ (Опціонально) Skills закоммічено до Git (Option C)
5. ✅ Команда може replicate setup (Option C)

---

**Version**: 1.0
**Last updated**: 2025-12-28
**Project**: violin.pp.ua
**Maintained by**: Claude Code + Perplexity AI
