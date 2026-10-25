# Test Failure Register

Use this register for recurring CI failures. A failure is not closed until the root cause, fix commit, and a regression check are recorded. Do not merge a PR while required checks or acceptance tests fail.

## Incident: diary emulator test used an invalid ADB command

- **Symptom:** The diary crop-and-rescan test stopped after tapping the Downloads row. ADB exited with status 127.
- **Root cause:** The command list already contained `shell`, then appended a second `shell` before `uiautomator dump`.
- **Fix:** Commit `3dde5052105d82c1c54fa5968d6c495baef62b54` removes the duplicate argument.
- **Regression prevention:** Added `.github/scripts/test_diary_emulator_script.py`, which checks the ADB command shape and the dump/pull/parse order before emulator allocation. It also verifies the workflow preserves failure reports.
- **Acceptance still required:** A fresh emulator run must select the fixture, crop it, rescan through the deterministic API, save both expected tasks, and verify the planner excludes tasks from other dates.

## Required incident-closing checklist

- [ ] Capture the exact failing step, command, exit code, and relevant log excerpt.
- [ ] Identify root cause rather than only retrying the failed run.
- [ ] Add a deterministic regression test for the root cause.
- [ ] Verify the regression test fails against the old behavior and passes with the fix where practical.
- [ ] Run all required CI checks on the fix commit.
- [ ] Link the fix commit and successful run here; do not close on a build-only pass.

## Incident: diary picker test tapped preview instead of selecting the file

- **Symptom:** Emulator run `40151883852` failed with `Diary filename disappeared after preview`; after tapping the preview-eye affordance and pressing BACK, the picker had exited to PadippuPal.
- **Root cause:** The test treated the clickable `Preview the file …` icon as a file-selection control. On this AOSP DocumentsUI build it launches a preview, and BACK exits the picker; the test then incorrectly looked for the filename in the app's UI tree.
- **Fix:** Commit `e9142247fdac2b3122943268ff84ff33c0d88e6e` changes the interaction to tap the actual filename row and, only if DocumentsUI remains open, inspect the resulting hierarchy for a real Open/Select confirmation or retry the filename tap. The script saves the row-action hierarchy for diagnosis.
- **Regression prevention:** Added a static regression test requiring filename-row selection and forbidding the preview-icon path.
- **Validation:** Pending CI on the fix commit. Do not close this incident or merge PR #21 until the Android emulator flow passes through crop, rescan, review, and planner save.
