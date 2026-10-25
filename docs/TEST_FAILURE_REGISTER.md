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

## Incident: smoke-script validation rejected the current picker parser helper

- **Symptom:** Workflow run `40153201804` passed JVM tests and APK build but failed before emulator allocation. `test_picker_dump_is_pulled_before_it_is_parsed` expected the obsolete string `ns=getnodes(path)`; the embedded parser actually defines and calls `nodes(path)`.
- **Root cause:** A static regression test asserted a literal helper call without keeping its expectation synchronized with the implementation. This stopped the real emulator test from running, so a harmless test drift blocked acceptance verification.
- **Fix:** Commit `de69bc5b5b0167aa0202db2ef41fa742783c1826` updates the expected call to `ns=nodes(path)` and checks that the helper is defined before the parser call.
- **Regression prevention:** Keep the dump-before-parse ordering assertion and verify the exact helper used by the embedded parser. Run script validation and the full emulator smoke test on the fix commit; a green static check alone does not close this incident.
- **Validation:** Pending CI. PR #21 must remain open until the emulator verifies picker selection, crop, rescan, review, and planner save.


## Incident: picker selection tapped a non-clickable filename label

- **Symptom:** Emulator run `40153864135` built the APK and passed JVM/static checks, but failed because DocumentsUI remained open after the filename tap and retry.
- **Evidence/root cause:** The uploaded `picker-selection-stuck.png` and matching UI hierarchy show DocumentsUI in its file-list layout. The filename is an `android.widget.TextView` with `clickable=false`; the test tapped the center of that label twice, so it never activated the file row. The thumbnail is the visible row target to the left of the label.
- **Fix attempt:** Commit `7f2dff3f7d562848c9a83a05409bdaeae1150403` changes the initial and fallback taps to target the thumbnail aligned with the filename row. Commit `8c96ac8484650967ab0d946b075dd6ca41e306a0` updates the static regression check to require the thumbnail-target interaction.
- **Regression prevention:** Static validation now checks for the thumbnail target rather than asserting that a non-clickable filename label is tapped. The end-to-end test must still prove that DocumentsUI returns to PadippuPal, opens crop UI, rescans, saves the expected tasks, and verifies planner contents.
- **Validation:** Pending a fresh CI run. This is a reasoned fix based on the uploaded screenshot/UI tree, not yet a verified end-to-end pass. Do not merge PR #21 until the full emulator flow passes.


## Incident: thumbnail tap used filename's vertical coordinate

- **Symptom:** Run `40154725685` still left DocumentsUI open after the thumbnail-target attempt; build and JVM checks passed.
- **Root cause:** Inspecting `picker-selection-stuck.png` shows the thumbnail centered near (80,630), while the filename TextView bounds are [189,685][660,742]. The test derived y=713 from the filename bounds and tapped blank space below the thumbnail. This explains why the earlier "thumbnail" fix did not select the file.
- **Fix:** Commit `92bdd6c3d48559ad7a94fbaac0c8ac94f4fdd2f0` changes the tap y-coordinate to filename top minus 55 pixels (and x to filename left minus 109 pixels), matching the observed thumbnail center. Commit `ff5b55efe49951daa03ea5fc080687ccd6efe4c5` updates the regression test to require these coordinates.
- **Validation:** Fresh emulator CI pending. The coordinate fix is evidence-based but not yet proven end-to-end; do not merge PR #21 unless the picker returns to PadippuPal and crop, rescan, and planner-save assertions all pass.


## Incident: picker tap remained above the file row

- **Symptom:** Emulator run `40155882991` passed JVM tests, APK build, and smoke-script validation, but the picker remained open after two taps at `(80,630)`.
- **Root cause from the uploaded UI hierarchy:** The fixture row bounds are `[0,641][1080,830]`; its thumbnail ImageView bounds are `[42,683][147,788]`. The test tapped at y=630, which is **above the row**, not on the thumbnail. The earlier coordinate calculation was wrong; prior claims that this coordinate matched the thumbnail were incorrect.
- **Fix:** Commit `1217e5c9745ded072f6367089638ef730468093d` parses the actual `com.android.documentsui:id/icon_thumb` node and taps the center of its live bounds for both the initial and fallback attempt, rather than deriving coordinates from the filename label.
- **Regression prevention:** Commit `bfdbba55e11a06edbd9ed184e540c4673e3506e0` updates the static regression test to require thumbnail-node lookup and center-of-bounds coordinates.
- **Validation:** Pending a fresh CI run. This corrects the proven coordinate error, but is not considered resolved until emulator CI selects the image and passes crop, rescan, review, and planner-save assertions. Do not merge PR #21 before that full pass.


## Incident: static regression assertion lagged behind picker fix

- **Symptom:** Run `40157302105` passed JVM tests and APK build but failed script validation, so the emulator was skipped.
- **Root cause:** The picker implementation and other assertions were updated to locate the actual `icon_thumb` node, but one old assertion still required the removed log text `Tap diary thumbnail/file-row target`. This was test drift, not an emulator result.
- **Fix:** Commit `de55dbe5ac863f82457bab0d962b50be5d91b923` removes that obsolete assertion while retaining checks for live thumbnail-node bounds and center-coordinate taps.
- **Validation:** Fresh script validation and emulator run pending. This incident does not close the underlying picker issue; do not merge PR #21 without the complete emulator flow passing.


## Incident: emulator fixture missing from DocumentsUI Downloads

- **Symptom:** Run `40164183979` passed JVM tests, APK build, and smoke-script validation, then failed in the real emulator because `PadippuPal-diary-test.jpg` was absent from the image-filtered Downloads listing. The screenshot shows DocumentsUI's Downloads view with an empty image list; the fixture push itself completed.
- **Root cause:** The test copied the JPEG into shared storage but relied on the deprecated `MEDIA_SCANNER_SCAN_FILE` broadcast to index it. On this Android 11 emulator, the file did not appear in the MediaStore-backed image list used by DocumentsUI, so the picker could not see it.
- **Fix attempt:** Explicitly register the fixture in `content://media/external/images/media` and verify the matching row exists before launching the app. If indexing fails, log both the file path and MediaStore query rather than failing later with a misleading picker-selection error.
- **Regression prevention:** Static smoke-script validation checks for explicit MediaStore registration and a query proving the fixture is indexed before the UI flow starts.
- **Validation:** Pending a fresh CI run. Do not merge PR #21 unless the fixture becomes visible, the picker returns to PadippuPal, and crop, rescan, review, and planner-save assertions pass.


## Incident: MediaStore fixture registration used unsupported columns and a rejected selection

- **Symptom:** Run [40165215787](https://github.com/Prav1525/Padippupal/actions/runs/40165215787) passed JVM tests, APK build, and script validation, but the diary emulator test stopped before opening the picker.
- **Root cause:** The fixture file was successfully pushed to `/sdcard/Download/PadippuPal-diary-test.jpg`, but the setup inserted it through the legacy `content://media/external/images/media` endpoint with unsupported `display_name` and `relative_path` columns. Android logged `Invalid column display_name`. The follow-up `content query --where "_display_name='PadippuPal-diary-test.jpg'"` was also rejected with `Invalid token PadippuPal`, so the test never verified indexing successfully.
- **Fix:** Remove the unsupported insert columns and verify the indexed row by querying the image table projection and matching the filename in the host-side output, avoiding the rejected selection expression.
- **Regression prevention:** Extend `.github/scripts/test_diary_emulator_script.py` to forbid those unsupported insert columns and the brittle `--where` form, and require the unfiltered projection check.
- **Validation:** Script regression checks and a fresh emulator run are required. Keep PR #21 open until the fixture is visible in DocumentsUI and the full crop, rescan, review, and planner-save flow passes.

## Incident: DocumentsUI exposed the fixture name as a content description

- **Symptom:** Run [40165802993](https://github.com/Prav1525/Padippupal/actions/runs/40165802993) passed JVM tests, APK build, script validation, and the general tutor UI smoke flow, but the diary flow failed while looking for the fixture in Downloads.
- **Root cause from the uploaded artifact:** The file was in fact visible in DocumentsUI. Its accessibility hierarchy exposed the filename through a node's `content-desc` (including file size and time), not the node's `text` attribute. The selection helper searched only for an exact `text` match and incorrectly reported the file missing. Inspection also found its bounds regex was over-escaped, preventing valid bounds from being parsed.
- **Fix:** Commit `348decd85f0088a32e5bd893ebb5414b0246730d` searches both `text` and `content-desc` for the filename and corrects the bounds regex to parse Android UI coordinates.
- **Regression prevention:** Commit `64c17a2482d4e9e1686ecedb3ccfd5bdb33fb257` adds static assertions for the content-description fallback and correctly escaped bounds pattern.
- **Validation:** Fresh CI is required to prove the picker selects the image and completes crop, rescan, review, and planner-save checks. This diagnosis is confirmed from the uploaded UI hierarchy, but the fix is not yet verified end to end. Do not merge PR #21 until the full emulator flow passes.

## Incident: DocumentsUI long-press selection assumption was wrong

- **Symptom:** Run [40166660424](https://github.com/Prav1525/Padippupal/actions/runs/40166660424) passed JVM tests, APK build, static diary contract checks, and the general tutor UI smoke flow. The diary flow found the fixture but failed after long-pressing it because no Select action appeared.
- **Root cause from the uploaded hierarchy:** The image-filtered Downloads screen used a grid. The fixture's outer row and thumbnail were exposed as non-clickable accessibility nodes, while a separate `Preview the file ...` action occupied a different child region. The test long-pressed the center of the row and incorrectly assumed that DocumentsUI would enter a selection mode with a Select action. The hierarchy did not support that assumption.
- **Fix attempt:** Replace the unsupported long-press/Select-menu strategy with a tap at the actual thumbnail child bounds, excluding the separate preview action, and explicitly wait for DocumentsUI to return before proceeding. Keep the corrected bounds regex and add regression assertions that reject the previous long-press strategy.
- **Regression prevention:** `.github/scripts/test_diary_emulator_script.py` now asserts thumbnail-targeted tapping and verifies the picker-return guard. The next emulator run must confirm this interaction actually returns the selected URI; if it instead opens a preview or stays in DocumentsUI, inspect the new screenshot/hierarchy and adjust based on that evidence.
- **Validation:** Fix is pushed but **not yet verified by a fresh emulator run**. Keep PR #21 open and do not merge until the picker returns and crop, rescan, review, and planner-save assertions all pass.

## Incident: DocumentsUI grid thumbnail is not a selectable target

- **Symptom:** Run [40167520653](https://github.com/Prav1525/Padippupal/actions/runs/40167520653) passed the APK build, curriculum tests, static diary contract checks, and general tutor smoke flow, but the diary emulator test remained in DocumentsUI after tapping the reported `icon_thumb` bounds.
- **Root cause from the latest hierarchy and screenshot:** In this run, `com.android.documentsui:id/icon_thumb` had the same full-card bounds as the non-clickable thumbnail container, and both were exposed as non-clickable. The previous strategy assumed this image view was a valid tap target; the hierarchy disproves that assumption. The separate preview icon is clickable but performs a different action.
- **Fix attempt:** Switch DocumentsUI to List view, find the fixture filename, walk up its accessibility hierarchy to the nearest clickable ancestor with valid bounds, and tap that row. Fail with the captured list hierarchy if no selectable row is exposed instead of guessing coordinates.
- **Regression prevention:** `.github/scripts/test_diary_emulator_script.py` now requires list-view selection via a clickable filename ancestor and rejects the non-clickable grid-thumbnail strategy.
- **Validation:** The change is pushed but still requires a fresh emulator run. Do not merge PR #21 until selection returns to PadippuPal and crop, rescan, review, and save all pass.


## Incident: DocumentsUI list row was present but exposed no clickable ancestor

- **Symptom:** Run [40168559516](https://github.com/Prav1525/Padippupal/actions/runs/40168559516) passed JVM tests, APK build, script validation, and the general tutor emulator flow, then failed at diary photo selection with `No clickable file-row ancestor found in DocumentsUI list view`.
- **Root cause confirmed from `diary-picker-list.xml`:** The filename TextView, its containing layouts, and `com.android.documentsui:id/item_root` are all marked `clickable=false`. The helper incorrectly treated accessibility clickability as proof of whether a row can receive a touch. The fixture is visible and its row bounds are available; this is not a missing-file or MediaStore problem.
- **Fix:** Commit `93f96630b56ac7ec889a835a2d01f60433a13ea5` locates the actual `item_root` containing the fixture and taps its body using the captured bounds, away from the separate preview control. It no longer requires a clickable ancestor.
- **Regression prevention:** Commit `7895e3a3272c388ed182ead18a6195a2234b4f84` replaces the old clickable-ancestor assertion with checks for row-body targeting and the app-return/crop guards.
- **Validation:** New CI run required. This is a targeted fix based on the captured hierarchy, not yet an end-to-end pass. Keep PR #21 open until photo selection, crop, rescan, review, and today's planner save all pass.


## Incident: DocumentsUI row-body tap did not select the file

- **Symptom:** Run [40169953811](https://github.com/Prav1525/Padippupal/actions/runs/40169953811) passed JVM tests, APK build, script validation, and the general tutor UI flow, then remained in Downloads after eight selection checks.
- **Root cause confirmed from the screenshot and `diary-picker-list.xml`:** The filename TextView, thumbnail, and `item_root` row all have `clickable=false`. Tapping the row body at `(424,735)` therefore did not activate selection. The only file-specific clickable control exposed by the hierarchy is `com.android.documentsui:id/preview_icon`, with content description `Preview the file PadippuPal-diary-test.jpg`. The prior fix incorrectly assumed a non-clickable row still handled touch input.
- **Fix attempt:** Commit `fc42023339a2559777aa74298745608d758e68b4` changes the test to locate the fixture's actual clickable preview control, tap its measured bounds, and capture the resulting preview UI; commit `0b8069ba9720d2ff92b320428b1fdf8c18e4e60f` corrects the bounds parser; commit `e641fe7652a97e9d60711bc51f4988cc8af8a894` updates the regression test to require this control and reject row-body taps.
- **Regression prevention:** The static test now checks the clickable preview target and the preview/result diagnostic checkpoints. The next emulator run must verify whether preview returns the URI directly or exposes an explicit Open/Select action; the test attempts common explicit confirmation labels if DocumentsUI remains active.
- **Validation:** These changes are pushed but **not yet verified by a fresh emulator run**. Do not merge PR #21 until the selected URI returns to PadippuPal and crop, rescan, review, and today's planner save all pass.


## Incident: picker preview control did not select or return the image

- **Symptom:** Run [40171192703](https://github.com/Prav1525/Padippupal/actions/runs/40171192703) passed JVM tests, APK build, script validation, and the general tutor smoke flow, but the diary test stayed in Downloads after tapping the preview control and checking eight times.
- **Evidence/root cause:** The saved diary-picker-list.xml marks com.android.documentsui:id/preview_icon as the separate “Preview the file …” affordance, while the post-tap hierarchy and screenshot remain on the unchanged Downloads list. The test confused a preview affordance with a selection action. The prior row-body coordinate (424,735) was also near the bottom padding of the filename node [189,685][660,742], rather than the center of the visible filename text.
- **Fix attempt:** Commit daf2bf5837d3b89b6b35ebf5d2bd767b6e1eb18d replaces the preview-control tap with the filename text helper, which taps the text node's computed center, and captures picker-selection-result.png immediately after interaction. Commit f23a07c208ffa2f77257fc9fe8a1338b2dd3d7ba changes the static regression test to require filename tapping and forbid the preview-icon strategy.
- **Validation:** Fresh CI is pending. This is an evidence-based interaction change, not a verified fix until the emulator proves the picker returns to PadippuPal and the crop, rescan, review, and planner-save assertions all pass. Do not merge PR #21 before that full pass.


## Incident: filename-bounds regex regression blocked emulator allocation

- **Symptom:** Workflow run [40182175498](https://github.com/Prav1525/Padippupal/actions/runs/40182175498) passed JVM tests and APK build but failed smoke-script validation. Three tests raised `Invalid filename/item row bounds` for valid bounds such as `[20,100][350,180]` and `[189,685][660,742]`; the emulator stage was skipped.
- **Root cause:** The bounds regex in `.github/scripts/ui_smoke.py` was over-escaped, so it expected literal backslashes instead of the square-bracket coordinates emitted by Android UIAutomator.
- **Fix:** Commit `a86a8ddfcd5095a2ae9cbf71eec6f7c4b4d9b3a5` corrected the regex. Follow-up commit `d8daf4c4f5441a1ea1c95996632dceacb0b6b61f` also makes the tap use the filename node's actual bounds rather than a potentially screen-wide `item_root` center, while retaining the double-tap retry.
- **Regression prevention:** `.github/scripts/test_diary_emulator_script.py` exercises valid bounds and asserts expected filename-column tap coordinates. CI must pass static validation and then prove the emulator returns from DocumentsUI and completes crop, rescan, review, and planner save.
- **Validation:** Pending the workflow run triggered by the follow-up fix. No merge until the complete emulator acceptance flow passes.
