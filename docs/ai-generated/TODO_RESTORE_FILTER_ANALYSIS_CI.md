# TODO: Restore Filter Analysis CI Workflow

**⚠️ TEMPORARY FILE - DELETE AFTER COMPLETION ⚠️**

## Problem
Disabled valuable `filter-analysis-ci.yml` workflow (301 lines) due to missing test files that were in gitignored `temp/` directory.

## Current Status
- **Disabled**: `.github/workflows/filter-analysis-ci.yml.disabled`
- **Temporary Fix**: `filter-analysis-ci-simple.yml` (basic Docker test)
- **Missing Files**: 
  - `temp/filter-testing/test_fast_filter_ci.py`
  - `temp/analysis-tools/video_comparison_test_library.py`

## Lost Valuable Features
- ✅ Random filter combination testing
- ✅ Specific filter pair testing via workflow_dispatch
- ✅ Performance benchmarking with timing
- ✅ Library accuracy validation
- ✅ Matrix testing across filter combinations
- ✅ Daily regression testing (cron schedule)
- ✅ Comprehensive reporting and status tracking

## Restoration Plan

### Step 1: Locate/Recreate Missing Files
```bash
# Check if files exist locally (they do)
ls -la temp/filter-testing/test_fast_filter_ci.py
ls -la temp/analysis-tools/video_comparison_test_library.py

# Move to committed location
mkdir -p tests/filter-analysis/
mv temp/filter-testing/test_fast_filter_ci.py tests/filter-analysis/
mv temp/analysis-tools/video_comparison_test_library.py tests/filter-analysis/
```

### Step 2: Update Workflow File Paths
```bash
# Edit .github/workflows/filter-analysis-ci.yml.disabled
# Replace all instances:
# OLD: temp/filter-testing/test_fast_filter_ci.py
# NEW: tests/filter-analysis/test_fast_filter_ci.py
# OLD: temp/analysis-tools/video_comparison_test_library.py  
# NEW: tests/filter-analysis/video_comparison_test_library.py
```

### Step 3: Test and Re-enable
```bash
# Test locally first
python3 tests/filter-analysis/test_fast_filter_ci.py --help

# Re-enable workflow
mv .github/workflows/filter-analysis-ci.yml.disabled .github/workflows/filter-analysis-ci.yml

# Test with BD
python3 scripts/bd_local_ci.py --docker
```

### Step 4: Verification
- [ ] Workflow runs successfully in CI
- [ ] Random filter tests work
- [ ] Performance benchmarking works  
- [ ] Matrix testing executes properly
- [ ] Manual workflow_dispatch triggers work

## Estimated Effort
- **Time**: 30-45 minutes
- **Risk**: Low (files exist, just need path updates)
- **Value**: High (comprehensive video filter testing)

## Delete This File After
- [ ] Filter analysis CI workflow restored
- [ ] All tests passing in CI
- [ ] Full functionality verified

**Created**: 2025-08-28  
**Context**: BD analysis of GitHub Actions failure in PR 22