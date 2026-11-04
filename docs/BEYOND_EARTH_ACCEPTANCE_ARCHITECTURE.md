# Beyond Earth acceptance test architecture

**Decision date:** 2026-11-04  
**Scope:** PR #182 only; Science → Beyond Earth original-image tutor acceptance.  
**Status:** Phase 1 implemented; CI verification pending. The fixture-preparation job split remains a follow-on within this same objective, not a claimed completion.

## Evidence driving the redesign

Run [41813853022](https://github.com/Prav1525/Padippupal/actions/runs/41813853022) built the debug APK, passed script/image-mapping and JVM tests, fetched all 19 original image blobs, booted Android, and installed the APK. It then failed before lesson setup completed.

The uploaded [failure artifact](https://github.com/Prav1525/Padippupal/actions/runs/41813853022/artifacts/13313714325) shows a system-level "System UI isn't responding" dialog. Logcat records an ANR in `com.android.phone`, high kernel time in `system_server`, repeated monitor contention in ActivityManager/WindowManager/AccessibilityManagerService, and a 16-second system_server GC. The emulator log records a 336,766 ms boot. The launch command itself returned `Status: timeout`.

The old runner explicitly used `-accel off` and `swiftshader_indirect` on an Ubuntu hosted VM without usable KVM. This forced TCG software CPU emulation. The evidence strongly supports infrastructure starvation/system-service contention as the immediate cause; it does **not** prove that the app is free of UI performance defects.

## Decision

Replace the TCG emulator with an Android x86_64 emulator running directly on a GitHub-hosted Intel macOS runner using Apple's Hypervisor.Framework. Use the maintained ReactiveCircus Android Emulator Runner action to install the API 35 AOSP image, create/boot the AVD, verify readiness, and run the existing Python tutor acceptance script. Keep the app APK build, JVM tests, original-image fixture, and actual screenshot assertions.

Why this is materially different:
- The old run emulated guest CPU instructions in software (`-accel off`); the new runner is expected to use the host hypervisor.
- The old workflow manually managed ADB transport, emulator boot, PackageManager readiness, and emulator process cleanup; the maintained runner owns those lifecycle operations.
- The acceptance script still drives the actual app and asserts the selected Science chapter, tutor lesson content, mapped image labels, and screenshot detail. No visual assertions are removed.

Android's official documentation states that macOS emulator VM acceleration uses Hypervisor.Framework and provides `emulator -accel-check` to verify it. See [Android Emulator hardware acceleration](https://developer.android.com/studio/run/emulator-acceleration). GitHub lists `macos-15-intel` as a standard Intel macOS runner; see [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Pipeline boundaries

1. **Fast validation/build:** Python helper checks, Kotlin/JVM tests, and exact debug APK build.
2. **Original-image fixture:** fetch the live manifest and all 19 original image bytes read-only; validate count, MIME type, non-empty bytes, and manifest mapping.
3. **Hardware-backed UI acceptance:** start the deterministic local fixture, run the exact APK on an accelerated Android API 35 emulator, navigate CBSE Class 6 → Science → Beyond Earth, and capture the actual tutor UI and hierarchy.
4. **Evidence:** always upload screenshots, UI trees, fixture logs, and emulator diagnostics. The release gate remains red unless the actual tutor screenshot and mapped image assertions pass.

**Remaining architecture improvement:** fixture preparation and Android UI execution still share one job in Phase 1. Split them into independent jobs connected by a versioned artifact containing the exact manifest plus original image bytes. This will ensure no production network/cold-start dependency exists in the emulator job. Do that without weakening the live-source provenance check. This is deliberately not marked complete in this commit.

## Guardrails

- Do not silently fall back to TCG/software CPU emulation if Hypervisor.Framework is unavailable. The emulator runner must fail rather than produce another misleadingly slow run.
- Keep all 19 original image bytes and their manifest mapping; do not replace them with generated placeholders or fixture-only synthetic image bytes.
- Do not loosen tutor navigation, image label, screenshot detail, or inline visual assertions to get green CI.
- A successful build or emulator boot is not visual acceptance. Inspect the actual tutor screenshot and hierarchy from the same tested commit.
- PR #182 stays open. No merge, production database write, deployment, or public release without explicit founder approval.

## Acceptance for this redesign

- [ ] Python/bootstrap tests pass.
- [ ] Kotlin/JVM tests pass.
- [ ] Exact debug APK builds.
- [ ] Fixture validates all 19 original images.
- [ ] Hardware-accelerated emulator reports ready and installs the exact APK.
- [ ] Actual tutor journey reaches Beyond Earth.
- [ ] Actual tutor screenshot visibly contains the mapped original image inline; labels and image-detail assertions pass.
- [ ] Screenshot and diagnostics are uploaded and inspected.
- [ ] Follow-on fixture artifact split is implemented and verified before calling the test architecture fully decoupled.
