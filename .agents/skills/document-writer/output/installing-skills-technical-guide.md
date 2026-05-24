# Installing Claude Code Skills: A Complete Technical Guide

Claude Code Skills are modular, reusable prompt templates that extend Claude Code's capabilities. Think of them as plugins or extensions that equip Claude with specialized knowledge for specific tasks—from marketing and SEO to podcast generation and document formatting.

---

## What Are Claude Code Skills?

A skill is essentially a well-crafted prompt stored as a Markdown file (typically named `SKILL.md`) that defines:

- **When to trigger** the skill (keywords and use cases)
- **How to behave** (detailed instructions and workflows)
- **What outputs to produce** (format, structure, quality standards)

Skills can include supporting files like:
- `evals/` — Evaluation criteria
- `references/` — Documentation and templates
- Helper scripts (Python, Node.js, Shell)

### Why Skills Matter

Without skills, Claude relies on general-purpose prompting. With skills, you get:
- **Consistent quality** — Built-in quality checks and standards
- **Specialized expertise** — Domain-specific workflows
- **Reusability** — Share across projects and teams
- **Version control** — Track changes and improvements

---

## How to Install Skills from Marketplace

The easiest way to install skills is through the built-in marketplace system.

### Step 1: Add a Marketplace

```bash
claude plugin marketplace add owner/repo-name
```

Example:
```bash
claude plugin marketplace add coreyhaines31/marketingskills
```

### Step 2: List Available Skills

```bash
claude plugin install --list
```

Or check the marketplace's `marketplace.json` file for available skills.

### Step 3: Install a Skill

```bash
claude plugin install skill-name
```

Example:
```bash
claude plugin install marketing-skills
```

### Verify Installation

```bash
claude plugins list
```

Installed skills appear in `~/.claude/skills/` as directories containing `SKILL.md`.

---

## How to Install Skills Manually

Sometimes you need to install skills not in a marketplace—perhaps from a GitHub repository, a download, or a custom skill you've created.

### Method 1: Clone and Copy

```bash
# Clone the skill repository
git clone https://github.com/username/skill-name.git

# Copy to your global skills directory
cp -r skill-name/* ~/.claude/skills/skill-name/

# Or copy to project-specific directory
cp -r skill-name/* /path/to/your-project/.claude/skills/
```

### Method 2: Direct Download

```bash
# Create the skill directory
mkdir -p ~/.claude/skills/my-custom-skill

# Download the SKILL.md file
curl -L -o ~/.claude/skills/my-custom-skill/SKILL.md \
  https://raw.githubusercontent.com/username/repo/main/SKILL.md
```

### Method 3: Symlink for Development

If you're developing a skill, symlink it for easy editing:

```bash
ln -s ~/my-skill-development/my-skill ~/.claude/skills/my-skill
```

### Verify Manual Installation

Check that the skill is recognized:

```bash
ls ~/.claude/skills/ | grep skill-name
```

You should see the skill directory containing at least `SKILL.md`.

---

## How to Create Custom Skills

Creating your own skill gives you complete control over Claude's behavior for specific tasks.

### Step 1: Choose the Right Structure

Skills typically follow one of these formats:

| Format | File | Description |
|--------|------|-------------|
| Simple | `SKILL.md` | Single file with all instructions |
| Extended | `SKILL.md` + `references/` | Main file plus supporting docs |
| Complex | Full directory | SKILL.md + scripts + evals + tests |

### Step 2: Write the SKILL.md

Every skill needs a `SKILL.md` file with frontmatter:

```yaml
---
name: my-custom-skill
description: When the user wants to [do something]. Also use when they say [trigger phrases].
metadata:
  version: "1.0.0"
  author: Your Name
  tags: [tag1, tag2]
---

# Skill Name

[Detailed instructions...]

## When to Use

- Use when [scenario 1]
- Use when [scenario 2]

## How It Works

[Step-by-step workflow...]

## Quality Standards

[Checklist or criteria...]
```

### Step 3: Define Triggers

Include clear trigger conditions in the description:

```yaml
description: >
  When the user wants to analyze code for security vulnerabilities.
  Triggers: "security audit", "check for vulnerabilities", "security review".
```

### Step 4: Add Supporting Files (Optional)

```
my-skill/
├── SKILL.md              # Main skill definition
├── evals/
│   └── evals.json        # Evaluation criteria
├── references/
│   └── patterns.md       # Reference documentation
└── scripts/
    └── analyze.py        # Helper scripts
```

### Step 5: Test Your Skill

1. Install it manually (see Method 1 above)
2. Test with various inputs
3. Refine the instructions based on results
4. Add to a marketplace if others might benefit

---

## Best Practices and Tips

### 1. Keep Skills Focused

Each skill should handle one specific task well. Don't combine unrelated functionalities.

**Good:** `copywriting` — focused on marketing copy
**Bad:** `copywriting-and-design-and-seo` — too broad

### 2. Use Clear Trigger Phrases

Make it obvious when to use your skill. Include 5-10 trigger phrases in the description.

```yaml
description: >
  When the user wants to write Python unit tests.
  Triggers: "write tests", "unit test", "add tests", "test coverage",
  "pytest", "unittest"
```

### 3. Include Quality Checks

Add a checklist or validation step:

```markdown
## Quality Check

- [ ] Function names are descriptive
- [ ] Tests cover edge cases
- [ ] No hardcoded values
- [ ] Error handling included
```

### 4. Document Edge Cases

Tell users what your skill CANNOT do:

```markdown
## Limitations

- Does not handle GUI testing
- Does not generate performance benchmarks
- Requires pytest installed
```

### 5. Version Your Skills

Use semantic versioning in metadata:

```yaml
metadata:
  version: "1.2.0"  # major.minor.patch
```

### 6. Share and Get Feedback

- Publish to a marketplace
- Add clear README with examples
- Include evaluation criteria for consistency

---

## Troubleshooting Common Issues

### Skill Not Recognized

```bash
# Check skill directory exists
ls ~/.claude/skills/ | grep skill-name

# Verify SKILL.md exists
cat ~/.claude/skills/skill-name/SKILL.md | head
```

### Skill Loading but Not Triggering

- Check trigger phrases in description
- Ensure frontmatter is valid YAML
- Verify no syntax errors in Markdown

### Conflicts Between Skills

If multiple skills have overlapping triggers, Claude will ask you to choose. To avoid this:
- Make trigger phrases more specific
- Use unique keywords per skill
- Check marketplace for duplicates

---

## Conclusion

Claude Code Skills transform Claude from a general-purpose AI assistant into a specialized tool for your exact workflow. Whether you're installing ready-made skills from the marketplace or creating custom ones, the skill system provides a powerful way to extend Claude's capabilities.

Start by exploring the marketplace, install a few skills relevant to your work, and don't hesitate to create custom skills when you find yourself repeatedly prompting Claude the same way.

**Next Steps:**
1. Explore available skills: `claude plugin install --list`
2. Install a skill that matches your use case
3. Create your first custom skill

---

*Generated with document-writer skill*
