# Troubleshooting

Common issues and how to recover.

## Installation Issues

### "Cannot write to .spec/ — permission denied"

**Cause**: The repository is on a read-only filesystem or the current user lacks write permissions.

**Diagnosis**:
```bash
ls -la .spec/ 2>&1 | grep -i permission
touch .spec/.test-write 2>&1
```

**Recovery**:
1. Check file permissions: `chmod -R u+w .spec/`
2. Verify the current user owns the repo or is in the repo's group
3. If running in CI/Docker, ensure the build user has write access to the repository
4. If the filesystem is truly read-only, install to a different location or use a writable clone

### "book-producer command not found"

**Cause**: Install didn't complete globally, or npm bin directory not in `$PATH`.

**Recovery**:
```bash
# Install globally
npm install -g book-producer

# Or add npm bin to PATH
export PATH=$(npm bin -g):$PATH

# Or use npx
npx book-producer install
```

---

## Workflow Issues

### ".branch-mapping.json is corrupted (invalid JSON)"

**Cause**: File was partially written or manually edited with syntax errors.

**Recovery**:
```bash
# Delete the corrupted file
rm .spec/.branch-mapping.json

# It will be recreated on next book init
# In chat:
# "Create a new book: My New Book"
```

### "state.json not found" or "state.json: permission denied"

**Cause**: State file was deleted, corrupted, or filesystem lost access.

**Recovery**:
```bash
# Check if the spec folder exists
ls -la .spec/<your-book-slug>/

# If missing, delete and reinit
rm -rf .spec/<your-book-slug>

# In chat:
# "Reinit the <your-book-slug> book idea"
```

### "Cannot resume my book — branch mapping doesn't recognize it"

**Cause**: The book was created on a different branch and isn't registered on your current branch.

**Diagnosis**:
```bash
cat .spec/.branch-mapping.json | jq '.branches'
```

**Recovery**:
```bash
# Option 1: Checkout the original branch
git checkout <original-branch>

# Option 2: Register on current branch (manual)
# In chat:
# "I'm on the <current-branch> branch now. Register cosmic-detective here."

# Option 3: View all books
# In chat:
# "List all my book ideas"
```

### "Chapters not assembling into manuscript"

**Cause**: Chapter files missing, in wrong location, or have invalid frontmatter.

**Diagnosis**:
```bash
# Check chapter location
ls -la <book-slug>/chapters/

# Check chapter frontmatter
head -15 <book-slug>/chapters/01-*.md
```

**Recovery**:
```bash
# Ensure all chapters are in the correct directory:
# <book-slug>/chapters/ at the REPO ROOT (not inside .spec/)

# Verify each chapter has valid frontmatter:
# Must include: chapter: <number>, title: "...", status: approved|draft

# In chat:
# "Assemble the manuscript. Check that all chapters are in <book-slug>/chapters/"
```

### "Manuscript file not created after assembly"

**Cause**: Assembly ran but didn't write the output file. Check permissions or disk space.

**Diagnosis**:
```bash
ls -la <book-slug>/manuscript-*

# Check disk space
df -h
```

**Recovery**:
```bash
# Ensure manuscript directory exists
mkdir -p <book-slug>

# Retry assembly in chat:
# "Assemble the manuscript again"

# If still missing, check for write errors:
# "Show the assembly log for any errors"
```

---

## Stage-Specific Issues

### Stage 1 (Concept)

**"state.json shows 'currentStage: 1-book-init' but I want to move to stage 2"**

In chat:
```
You: "I've approved the book idea. Let's move to stage 2 planning."

Claude: (reads state.json, updates it, writes 02-plan.md)
```

State advances automatically when you approve in chat. No manual intervention needed.

### Stage 4 (Chapters)

**"My chapters aren't being saved"**

Ensure chapters are written to `<book-slug>/chapters/` at the repo root, not inside `.spec/`.

```bash
# Correct:
cosmic-detective/chapters/01-chapter.md

# Wrong (won't work):
.spec/cosmic-detective/chapters/01-chapter.md
```

**"The final manuscript is missing some chapters"**

Check that each chapter has `status: approved` in its frontmatter. Unapproved chapters ('status: draft') are included in current v0.1.0 but reported separately in assembly summary.

---

## File Corruption & Recovery

### "General JSON parsing error"

If any `.json` file (state.json, .branch-mapping.json, chapter-memory.json) is corrupted:

**Recovery**:
```bash
# Create a backup
cp <file>.json <file>.json.backup

# Delete the corrupted file
rm <file>.json

# Reinit the affected concept or resume in chat:
# "Reset my progress and reinit"
```

---

## Version & Compatibility

### Upgrading from v0.1.0 to v0.2.0

See [UPGRADING.md](UPGRADING.md) for migration steps.

### Node Version

book-producer requires **Node 18 or higher**.

```bash
node --version
# Should output v18.x.x or higher

# If you have an older version, upgrade:
# See https://nodejs.org/en/
```

---

## Still Stuck?

If you encounter an issue not listed here:

1. Check [CHANGELOG.md](CHANGELOG.md) for known limitations in v0.1.0
2. Review the [README.md](README.md) "Persistence" and "Branch Mapping" sections
3. In chat, share the error message and your directory structure:
   ```bash
   tree .spec/
   tree <book-slug>/ | head -20
   cat .spec/.branch-mapping.json | jq .
   ```
4. Open an issue on GitHub with reproduction steps
