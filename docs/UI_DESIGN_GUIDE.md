# PadippuPal UI design and aesthetic standards

This is the durable design guide for all future PadippuPal interface work. Read it before designing or changing UI, alongside `.github/testing-regression-checklist.md` and `docs/TESTING_ERRORS.md`. Treat these as product constraints, not optional inspiration.

## Design goal

Build a calm, polished learning experience that feels like a patient human teacher: clear, warm, focused, modern, and easy to use on a real phone. Visual design must support learning, not compete with it. Prefer a few strong decisions consistently applied over decorative elements added screen by screen.

## Research baseline

Use the official Android guidance as the primary implementation reference:
- [Material 3 in Jetpack Compose](https://developer.android.com/develop/ui/compose/designsystems/material3) — typography, color roles, component emphasis, shapes, accessibility and theming.
- [Android touch-target guidance](https://support.google.com/accessibility/android/answer/7101858) — interactive targets should generally be at least 48 × 48 dp.
- [Adaptive app guidance](https://developer.android.com/develop/adaptive-apps/guides/use-window-size-classes) — layouts should respond to available window size instead of assuming one fixed screen.

If this guide conflicts with current official Android accessibility guidance, follow the current official guidance and update this document.

## Visual principles

1. **One clear job per screen.** The tutor screen teaches. Subject, chapter, topic and language are selected before entering it. Do not duplicate those selectors on the teaching screen.
2. **Teach in one continuous flow.** Spoken explanation, synchronized word highlight, examples and relevant animation belong in the lesson flow. Do not put teaching animation in a separate floating overlay, modal, or unrelated card.
3. **Use the viewport deliberately.** Avoid both cramped content and unexplained empty areas. The transcript should scroll independently when needed; checkpoint actions remain visible at the bottom above system navigation. Use constraints and measured layout behavior rather than arbitrary spacer piles or fixed heights.
4. **Hierarchy before decoration.** Establish hierarchy with type scale, spacing, weight, alignment and restrained surface contrast. Avoid too many cards, borders, pills, shadows, gradients, icons or competing accent colors.
5. **Readable before tiny.** Do not shrink labels to make a crowded layout fit. Simplify controls, shorten secondary text, or reflow the layout first. Never use 8–10 sp for meaningful lesson context or essential instructions.
6. **Consistent alignment.** Align titles, body copy, animation edges and controls to a small set of shared horizontal guides. Use a consistent spacing scale; default to multiples of 4 dp, with 8 dp as the small rhythm and 16 dp as a common phone inset.
7. **Accessible interaction.** Interactive targets should be at least 48 × 48 dp where practical, with adequate separation. Provide meaningful content descriptions, visible focus/pressed states, readable contrast and support for font scaling. Do not reduce hit areas just to make controls look smaller.
8. **Responsive by design.** Check compact phone dimensions, larger phones and landscape/large-window behavior when supported. Respect status/navigation bars, display cutouts, IME and system font scaling.
9. **Motion explains change.** Animations should be purposeful, brief, non-blocking and connected to the lesson. Respect reduced-motion/accessibility needs when applicable. Never let an animation delay speech, hide the active sentence, or compete with word highlighting.
10. **State is truthful.** Loading, speaking, paused, checkpoint, complete and error states must be distinct and accurate. Never show “preparing” after content is ready or make a failed voice attempt look completed.

## Typography system

Use Android's Material 3 type scale as a starting point; apply a smaller, consistent subset rather than choosing unrelated sizes for each component.

| Role | Starting size / line height | Use |
|---|---:|---|
| Screen title | 22 / 28 sp | Major screen title when space allows |
| Section title | 18–20 / 24–28 sp | Lesson/checkpoint heading |
| Lesson body | 16 / 24 sp | Primary teaching text |
| Supporting body | 14 / 20 sp | Secondary explanation or metadata |
| Compact label | 12 / 16 sp | Status labels and secondary control text |
| Minimum label | 11 / 16 sp | Dense metadata only, never core instructions |

Use the platform's readable sans-serif font by default unless a tested, bundled font has a clear product benefit. Keep body copy at a comfortable line height (normally around 1.4–1.55× font size). Avoid long all-caps labels; reserve uppercase for short, low-emphasis status labels. Use font weight to communicate hierarchy, not to decorate every sentence. Verify Tamil and mixed Tamil/English glyph rendering before adopting any custom font.

## Color and contrast

- Keep the existing PadippuPal navy, blue and light neutral identity unless a deliberate, reviewed palette change is approved.
- Define/reuse semantic roles (primary action, background, surface, primary text, secondary text, success, warning, error) rather than adding near-duplicate colors ad hoc.
- Use a strong text/background contrast. Do not rely on color alone to convey state.
- Use the accent color for active word highlighting and primary actions; avoid making every icon and label equally saturated.
- Disabled states must remain legible and must not look active.
- Check both light and dark system appearance if the app supports both.

## Spacing, shape and density

- Use a 4 dp base grid; common increments are 4, 8, 12, 16, 24 and 32 dp.
- On phone screens, start around 16 dp horizontal content margins; use 20–24 dp only where the content needs more breathing room and the viewport permits it.
- Group related items closely; add more space between unrelated groups. Keep a heading closer to the content it introduces than to the next section.
- Use a restrained corner-radius system (for example 8, 12, 16 and 24 dp) with meaningfully different roles. Do not round every nested element.
- Use elevation only when it clarifies layering. A full-screen lesson should not become a stack of floating cards.
- Prefer one primary action per decision. Secondary actions should be visually quieter but still easy to find and tap.

## PadippuPal tutor screen contract

- The header is a compact command bar (target 48–52 dp high). Keep Back and playback controls accessible; brand/topic text must be comfortably readable and must not be compressed to fit. Use concise topic text and balanced control spacing before shrinking type.
- Header visual icons may be around 20–24 dp, but their interactive hit areas must remain at least 48 dp.
- The lesson transcript gets the remaining vertical space and scrolls independently. Do not render faded previews of future segments.
- The active spoken sentence is the primary reading focus. Word highlight follows actual speech timing; it must not race ahead before playback is heard.
- Show only relevant in-flow visuals for the current concept. Keep animation size and complexity proportional to available space and current spoken content.
- Checkpoint question and its three actions (I understand, Explain again, I have a question) stay together, pinned below the transcript and above system navigation. Do not let an animation create a large dead zone or push the controls off-screen.
- No unnecessary instruction such as “Tap any word to hear its pronunciation again” when it is not part of the intended teaching interaction.
- Avoid controls that duplicate choices already made on the previous screen. Do not add overlays or decorative boxes just to fill empty space.
- Preserve navigation, pause/resume, stop, retry/error handling, question flow and accessibility semantics during redesign.

## Required design workflow

Before changing a screen:
1. Read this document and the current testing checklist/error log.
2. Inspect the real screen and relevant Compose hierarchy, state transitions, theme and component APIs. Identify the root cause of the visual issue.
3. Check official Android guidance and relevant platform conventions when selecting typography, spacing, accessibility or adaptive behavior. Avoid copying a Dribbble/marketing mockup without validating usability.
4. Define the screen's job, hierarchy, content priorities, viewport behavior and acceptance criteria before coding.
5. Make one coherent design pass. Do not repeatedly tweak a single padding value without checking the layout constraints causing the symptom.
6. Build and test the actual app. Inspect fresh screenshots from the exact tested commit, not generated mockups or screenshots from an older build.
7. Check live lesson and checkpoint states, small and large viewports, system bars, keyboard, scroll behavior, and all essential actions. Inspect text at normal and enlarged system font settings when practical.
8. Run the required tests using the testing checklist. Before every test run, read `docs/TESTING_ERRORS.md` and `.github/testing-regression-checklist.md`; log meaningful failures and corrective actions.
9. Report statuses accurately: **Implemented** means code changed; **Built** means compilation succeeded; **Tested** means named tests passed; **Visually verified** means the exact build's screenshots/behavior were inspected. Never imply one status proves another.

## Definition of done for a UI change

- The screen's purpose and hierarchy are immediately clear.
- No unexplained large empty areas, clipped content, overlaps, hidden controls or awkward text truncation.
- Typography, line height, spacing, color, alignment and component shapes follow this guide consistently.
- Touch targets, contrast, content descriptions, system bars and font scaling are respected.
- All relevant states and interactions still work.
- Fresh screenshots from the exact candidate commit have been inspected.
- Required automated tests pass, failures are recorded, and the PR remains open until all acceptance criteria pass.


## Visual taste and art direction — beyond alignment

Good-looking UI is not achieved by aligning every element and choosing a nice font. It comes from the combined feeling of composition, visual weight, rhythm, restraint, material, color, shape, and the product's personality. Review the screen as a whole at first glance, then inspect individual details.

### Lessons from product-design practice

- **Make the content the hero.** YouTube's design team explicitly describes reducing clutter, removing redundant actions and keeping the content central. For PadippuPal, the lesson sentence and its concept visual are the hero; controls should support teaching without competing for attention. See [YouTube's five design principles](https://blog.youtube/inside-youtube/design-principles-use-put-creators-center-stage/).
- **Create one coherent visual voice.** Use a deliberate palette, repeatable typography, consistent icon style, and related corner radii. Do not make every component look individually fashionable; the screen should feel like one designed product.
- **Use contrast to create composition.** Decide what should be noticed first, second and third. Reserve the strongest contrast, largest type, richest color and most prominent surface for the current learning task or primary action. If everything is bold, colorful, elevated or oversized, nothing is important.
- **Use whitespace with intention.** Empty space is useful when it separates groups, gives a focal point room, or improves reading. It is a defect when it leaves the lesson stranded in a corner or separates the animation from the checkpoint with no purpose. Judge the balance of the whole screen, not padding values in isolation.
- **Design a recognizable personality.** PadippuPal should feel calm, encouraging, intelligent and teacher-like—not like a generic dashboard, a game lobby, a corporate admin tool, or a collection of cards. Use warmth through tone, subtle color, friendly shapes and carefully chosen illustrations, rather than emoji overload or decorative clutter.
- **Treat shape as a system.** Buttons, containers, icons and illustrations should share a consistent geometry. Larger nested surfaces may use larger radii; small controls should not be rounded randomly. Use shadows and borders only when they clarify grouping or depth.
- **Use color semantically and sparingly.** A neutral canvas allows lesson text and the active highlight to stand out. Accent color should signal interaction, current focus, or meaningful state—not decorate every surface. Gradients and ambient effects are optional art direction, never a substitute for hierarchy.
- **Make illustrations feel art-directed.** Keep line weight, perspective, scale, palette and level of detail consistent. A teaching animation must be visually related to the concept and integrated with the spoken explanation. Avoid mixing unrelated clip-art, emoji, stock icons and illustration styles on one screen.
- **Motion needs choreography.** Use motion to show cause and effect, focus attention, or make a state change understandable. Keep transitions short and subtle, and never let motion delay speech or cause the highlight to get ahead of the voice.
- **Polish is cumulative.** Review small details together: baseline alignment, icon optical centering, button label balance, text wrapping, edge spacing, selected/disabled states, separators, animation pacing and system-bar insets. A handful of coherent refinements beats a pile of effects.

### Aesthetic review ritual

Before approving a screen, do these passes in order:

1. **Three-second glance:** Without reading details, can a person immediately tell what this screen is for and where to look first?
2. **Silhouette and balance:** Squint or view a small screenshot. Are the visual masses balanced? Is the focal content centered in the usable area, or is one region unexpectedly empty/heavy?
3. **Hierarchy in grayscale:** Temporarily judge the screen without relying on color. Are size, weight, spacing and placement enough to communicate priority?
4. **Color discipline:** Is the accent color scarce and meaningful? Are there too many competing surfaces, borders, shadows or saturated elements?
5. **Typography and rhythm:** Do headings, body text and labels have distinct roles? Is spacing consistent, and are related items visibly grouped?
6. **Personality and coherence:** Does the interface feel warm, calm and distinctive to PadippuPal? Do icons, illustrations, controls and animation belong to the same visual language?
7. **Real-device check:** Inspect the actual screenshot at normal phone size. Check long topic names, Tamil/Tanglish text, large font settings, system bars and the keyboard. Do not approve based only on a zoomed-in emulator or source code.
8. **Function check:** Confirm visual polish has not hidden essential actions, weakened touch targets, interrupted teaching or made state unclear.

### YouTube study queue

Use YouTube videos as visual-analysis exercises, not as templates to copy blindly. Search links are intentional so the team can choose currently available uploads and compare multiple explanations:

- [Steve Schoger — Refactoring UI design talk](https://www.youtube.com/results?search_query=Steve+Schoger+Refactoring+UI+design+talk): observe before/after transformations and note how hierarchy, contrast, spacing, shadows and surface treatment work together.
- [Steve Schoger — How to Think Like a Visual Designer](https://www.youtube.com/results?search_query=Steve+Schoger+How+to+Think+Like+a+Visual+Designer): practise explaining *why* a screen looks weak before choosing a fix.
- [Mobile app UI/UX design critiques and audits](https://www.youtube.com/results?search_query=mobile+app+UI+UX+design+critique+visual+hierarchy+typography): pause before the reviewer reveals changes; write down the three most important problems first.
- [Mobile app art direction, color and typography](https://www.youtube.com/results?search_query=mobile+app+visual+design+art+direction+color+typography): compare restrained, content-first designs with decorative, high-noise designs.
- [Material 3 Compose design system](https://developer.android.com/develop/ui/compose/designsystems/material3): use this as the implementation reference after learning from visual examples.

For each useful video, extract a transferable principle and test it against PadippuPal's learning goals. Do not copy another app's palette, layout, gradients or trendy effects simply because they look attractive. A visual idea is accepted only if it improves clarity, calmness, lesson focus, accessibility and consistency on the real device.

### Design decision record

When a substantial aesthetic change is made, briefly record in the PR description or relevant project notes:
- the visual problem observed in the real screenshot;
- the intended mood and hierarchy;
- the design principle applied and why;
- the states and device sizes inspected;
- the screenshot/test evidence and any remaining trade-offs.

This makes design reasoning reusable rather than relying on memory or repeated subjective tweaks.
