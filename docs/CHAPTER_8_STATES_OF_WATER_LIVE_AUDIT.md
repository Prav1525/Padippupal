# Chapter 8 — A Journey through States of Water: live DB audit (initial pass)

**Status:** In progress; do not publish from this audit.  
**Board/class/subject:** CBSE / Grade 6 / Science  
**Source row:** `ed0b5f40-e9e0-474d-82ac-9681b0f4c1cd`, NCERT Curiosity Class 6 Science — Chapter PDF (`fecu108.pdf`), database `page_count=20`.  
**Important discrepancy:** An earlier chapter lesson JSON/reference summary described 24 pages, but the live `sources` row says 20 pages. Use the source row and actual PDF page images as canonical; investigate this discrepancy before asserting page references.

## Live DB findings

A read-only query of `syllabus_topic_syntheses` for this exact source found approved page-part rows and broad draft topic rows. All queried rows reported `validation_status=passed`, which is not sufficient evidence of pedagogical correctness.

### Approved page-part synthesis defects

- **Part 1, page 1** (`639617486eb0820a36331fdb95d8dcade0e81ccf363136691470434f81191857`): caption joins the lemonade/ice observation with activity text about water drying from utensils. Needs clean segmentation and a coherent question/observation sequence.
- **Part 2, page 4** (`907f3b51ed586460ea71fb2e16bdae9946301a6b4543422ed8349fe328568e57`): caption includes activity heading “8.2 Another Mystery” and textbook instructions as if they were explanation. Must cleanly teach condensation on the outside of a cold tumbler.
- **Part 3, page 7** (`8bf9de88a71cad07fc1a84c7aab4269cdaac93529c3eeafe3a437b68898478d9`): caption contains page number/running header “A Journey through States of Water 149” and repeated instruction fragments.
- **Part 4, page 8** (`36f2c57a7183a5182790b4d1729d61a0f9dd1d9e249866c0719fdf3f654c9b6c`): table text is flattened into a string, with OCR contamination “Chapter 8.indd 150 10/4/2024 3:12:06 PM” and page header. The state/property table needs structured, legible rows and correct source checking.
- **Part 5, page 10** (`3c3dc16a292650570da2d8b123a14fd7a2f2ddb3e9431192efc151b25d09933c`): activity steps about bottle cap/plate are joined with a later heating prompt; split into evaporation-rate experiment and state-change explanation.
- **Part 6, page 14** (`3ddc9bbe8a6c235569b2ff49998c3c7aace065221905682546ddcbfb7bbeaf22`): text jumps from the earthen-pot story to a nested-pot construction instruction; needs staged explanation of evaporation and cooling, with no unsupported claims.
- **Part 7, page 15** (`571e27f1fb242a908723d03fb0942a1bdd3946a6bc1e7d92e7eb2d91fe14c51a`): caption combines surahi, hail/snow and a broken “(clouds) above the water in the bottle” fragment. Split distinct concepts and verify their source context.
- Other approved page-part rows exist (including Part 8 on page 19); complete full row-by-row review before calling the chapter covered.

### Broad draft synthesis topics

The query returned these draft topics with `page_start=1,page_end=20`, despite narrow concept scopes:
- `Introduction to Water States` (`21fad43095833473b0e1b277b6882ef148546ffd264a702822c7b34326f15183`)
- `Investigating Water's Disappearing Act` (`8bd6eb07f98ed131f9a161bfece8c222111544b7d4b91334146d6dd9d82705ea`)
- `Properties of Solid, Liquid, and Gas` (`3316953d920ff7504c7b3639e715a73d36aadd100bebd5d44989bf990777a80d`)
- `Melting and Freezing` (`644df95b043309f349f6f40b0eeebbd7595875730b82aa4ce7a89ef9ddaf3345`)
- `Condensation and Water Droplets on Tumblers` (`f79e474cc44aa5a328e52ccb38f3ae53cf06125f0346fe9716bbe4fa9c7bc381`)
- `Cooling Effect of Evaporation` (`53c88a23a16b9456a517d4902bd7136acb218a28e783429eb5fa9356fab48f8b`)
- `Factors Affecting Evaporation Speed` (`5468f584cf5e2ba6df636fd5f60d793064825c2d58e2365fd14c685123972fcc`)
- `Clouds, Rain, and the Water Cycle` (`253479d48fa652e06a640e166a76e79bcb50eed5d6fc7246e02ce95dc1d9f5ac`)

These topics overlap the approved page-part rows, so avoid showing duplicate lesson entries or creating duplicate visuals. Build a mapping from each draft concept to exact source chunk/page spans and lesson steps; use a new version/supersession mechanism instead of mutating approval status.

## Source-grounded visual storyboard to validate

1. **Ice cube in lemonade / states:** ice cube in glass; same substance, solid ice and liquid water. Show melting only after source context supports it.
2. **Water seeming to disappear:** small puddle/plate with water vapour rising; label evaporation. Avoid implying water vanishes or seeps through metal.
3. **Cold tumbler droplets:** show vapour in surrounding air contacting cold outer glass and condensing into droplets. Do not draw water leaking through the glass.
4. **States comparison:** three-column solid/liquid/gas table with shape, flow and spreading properties; preserve distinctions and verify exact textbook table.
5. **Evaporation experiment:** same amount of water in a small bottle cap and a wider plate; keep amounts controlled and only state results supported by the source.
6. **Cooling effect of earthen pot:** water moving through porous earthen wall and evaporating from outer surface, with heat leaving the pot/water. Validate mechanism and wording against source.
7. **Clouds/rain/water cycle:** evaporation → cooling/condensation → clouds → precipitation → collection; avoid overclaiming that every cloud/rain event follows one simplistic path.
8. **Chapter closing:** integrate water-state changes and everyday examples without introducing an unverified extra fact.

Use plain teacher-drawn 2D sketches directly in the tutor's continuous vertical text flow. No floating overlay, detached card, mini-game, or unrelated decorative visual.

## Next steps
- Reconcile draft and approved row inventories and check exact source chunk text/page spans.
- Review actual source page images; investigate the 20-page source-row vs 24-page lesson reference discrepancy.
- Check all active visual rows for this lesson and flag any generic or mismatched assets.
- Prepare a replacement synthesis/storyboard proposal only; do not write production rows or change approval states in this autonomous loop.
- Add regression tests for OCR page headers/timestamps and specific visual mapping; run exact-SHA CI and inspect fresh tutor screenshots.
