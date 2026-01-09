# Phase 2 Implementation Plan

## Completed (Phase 1)

✅ Consolidated duplicate helper functions
✅ Created utils/helpers.py with 4 consolidated functions
✅ Updated 8 command files to use consolidated helpers
✅ Removed ~180 lines of duplicate code
✅ Tested successfully (roadmap command)

## In Progress (Phase 2)

🔄 Add `skills create --ai-enhance` flag ✅ DONE
🔄 Add `workflow create --ai-enhance` command - IN PROGRESS
🔄 Deprecate `meta generate` commands - PENDING
🔄 Update documentation - PENDING

## Implementation Details

### 1. Skills Create --ai-enhance ✅

- Added `--ai-enhance` flag to `skills create` command
- Added `--ai-provider` option (auto/meta/openai/anthropic/azure)
- Added `--description` option (required with --ai-enhance)
- Fallback to template if AI unavailable
- Uses `ai.generate_skill()` method
- Properly handles AI-generated content vs template content

### 2. Workflow Create --ai-enhance (Next)

- Add new `workflow create` command to workflow.py
- Options:
  - `workflow_id` (argument)
  - `--description` (required with --ai-enhance)
  - `--ai-enhance` (flag)
  - `--ai-provider` (choice: auto/meta/openai/anthropic/azure)
  - `--template` (choice: sequential/parallel/conditional)
  - `--force` (overwrite existing)
- Template types:
  - sequential: Steps run one after another
  - parallel: Steps run concurrently
  - conditional: Steps with conditions/branches
- Uses `ai.generate_workflow()` method
- Creates `.parac/workflows/{workflow_id}.yaml`

### 3. Deprecate Meta Generate (Next)

- Add deprecation warnings to `meta generate agent` command
- Add deprecation warnings to `meta generate workflow` command
- Guide users to use `paracle agents create --ai-enhance`
- Guide users to use `paracle workflow create --ai-enhance`
- Update docstrings with deprecation notices

### 4. Documentation Updates (Future)

- Update CLI reference documentation
- Update AI generation guide
- Create migration guide
- Update examples in docs/

## Files to Modify

- [x] packages/paracle_cli/commands/skills.py - MODIFIED ✅
- [ ] packages/paracle_cli/commands/workflow.py - TODO
- [ ] packages/paracle_cli/commands/meta.py - TODO
- [ ] docs/users/ai-generation.md - Future
- [ ] docs/technical/cli-reference.md - Future
