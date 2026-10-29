# CBSE Class 6 Science — Visual Blueprint Catalogue

**Status: design inventory only; not proof of live database coverage or textbook verification.** This catalogue lists the 36 science lesson blueprints currently present in `backend/interactive_lessons.json`. That file states science concepts must be checked against the official NCERT Curiosity textbook. Inspect the exact edition and page before marking a lesson verified.

## Drawing contract
Every sketch is inline in the flowing explanation, simple original 2D, with labels/arrows and only scientifically justified relationships. No floating overlay, detached card, or generic circle fallback as the final science visual. If the selected teaching beat lacks evidence, mark `needs_review` rather than guessing.

| Chapter | Topic | Intended drawing / key visual evidence | Review cautions |
|---|---|---|---|
| The Wonderful World of Science | Observation and fair tests | Two matched seedlings/containers; highlight the single changed variable; hold other conditions visibly constant | Do not imply an experimental result not observed |
| The Wonderful World of Science | Question to evidence | Question → prediction → test → observation → evidence chain | Keep prediction distinct from measured result |
| The Wonderful World of Science | Patterns in nature | Three observed examples with a common feature highlighted | Do not claim a universal pattern from one example |
| Diversity in the Living World | Classifying living things | Branching classification by visible traits; one example organism per branch | Classification criteria must match lesson/source |
| Diversity in the Living World | Plant diversity | Labelled silhouettes of distinct plant forms (e.g. herb/shrub/tree/climber/creeper only if covered) | Do not use labels absent from approved lesson |
| Diversity in the Living World | Habitats and adaptations | Organism and habitat paired with one labelled adaptation | Avoid claiming every member of a group has the same adaptation |
| Mindful Eating: A Path to a Healthy Body | Balanced meal | Plate divided into food groups named by source | Use source-approved categories; avoid medical advice |
| Mindful Eating: A Path to a Healthy Body | Nutrients in food | Food examples grouped by nutrient with simple labels | One food may contain multiple nutrients; don't imply exclusivity |
| Mindful Eating: A Path to a Healthy Body | Digestion and healthy habits | Simple digestive pathway: mouth → food pipe → stomach → intestines | Check anatomy order and terminology |
| Exploring Magnets | Magnetic and non-magnetic materials | Magnet near sample objects; two evidence-based groups | Don't label material magnetic without a valid example |
| Exploring Magnets | Poles attract and repel | Two bar magnets with N/S labels; unlike poles attract, like poles repel | Arrow directions must be correct |
| Exploring Magnets | Magnetic field | Bar magnet with curved field lines and direction arrows | Field lines are a representation, not physical strings |
| Measurement of Length and Motion | Measure length correctly | Ruler with zero aligned to object end; mark start/end | Show parallax only if taught |
| Measurement of Length and Motion | Standard units | Same length expressed in approved units with conversion relationship | Verify conversion factors |
| Measurement of Length and Motion | Describe motion | Object at successive positions along a path; time/direction labels when given | Don't infer speed without distance/time data |
| Materials Around Us | Sort materials by properties | Property labels feeding into groups; examples grounded in lesson | Properties can overlap; avoid false exclusivity |
| Materials Around Us | Soluble and insoluble | Two containers with labelled solute/water and observed dissolved/undissolved state | Don't imply all substances dissolve equally |
| Materials Around Us | Choose a material for a job | Job → required property → candidate comparison | Choice must follow evidence |
| Temperature and its Measurement | Read a thermometer | Enlarged scale with liquid level and labelled reading | Use plausible scale and exact unit |
| Temperature and its Measurement | Compare temperatures | Two thermometers on the same scale with source-supported readings | Scale increments and units must match |
| Temperature and its Measurement | Safe temperature measurement | Appropriate thermometer use with safety boundaries | Never present unsafe handling as recommended |
| A Journey through States of Water | Solid, liquid and gas | Three particle boxes: tightly ordered, close/mobile, widely spaced | Schematic model; preserve distinctions |
| A Journey through States of Water | Melting and freezing | Ice ↔ water with heat removed/added arrows | Don't reverse heat-flow arrows |
| A Journey through States of Water | Evaporation and condensation | Liquid surface particles escaping; vapour cooling to droplets | Distinguish evaporation from boiling if mentioned |
| Methods of Separation in Everyday Life | Handpicking and sieving | Handpicking larger unwanted pieces; sieve retaining larger particles | Example sizes/materials must fit |
| Methods of Separation in Everyday Life | Sedimentation and decantation | Mixture settles; clear upper liquid poured off above sediment | Show settling before pouring |
| Methods of Separation in Everyday Life | Filtration and evaporation | Funnel/filter residue/filtrate; evaporation dish leaving dissolved solid | Don't confuse filtration with dissolving |
| Living Creatures: Exploring their Characteristics | Characteristics of living things | Source-supported examples of growth, nutrition, response, reproduction, etc. | Include only characteristics taught |
| Living Creatures: Exploring their Characteristics | Response to stimuli | Stimulus → organism response with a source-approved example | Don't overgeneralise one organism's response |
| Living Creatures: Exploring their Characteristics | Life cycles | Stage sequence with arrows; organism-specific stages | Correct stage order required |
| Nature's Treasures | Natural resources | Examples grouped by source-defined resource type | Don't misclassify manufactured products |
| Nature's Treasures | Water conservation | Water-use points connected to practical saving actions | Keep advice relevant and fact-based |
| Nature's Treasures | Reduce, reuse, recycle | Three distinct actions with one example each | Don't treat reuse and recycle as synonyms |
| Beyond Earth | Earth, Moon and Sun | Labelled Sun, Earth, Moon with separate orbit paths and schematic note | Moon orbits Earth; do not imply otherwise |
| Beyond Earth | Day and night | Sunlight on Earth; illuminated/dark halves; rotation direction if taught | Verify rotation arrow |
| Beyond Earth | Phases of the Moon | Sunlight direction, Earth, Moon positions and visible lit shapes | Phases are not caused by Earth's shadow except eclipses |

## Build and review order
1. Inspect the official NCERT Curiosity edition and record page/edition for each chapter.
2. Compare each row against approved synthesis teaching steps.
3. Replace placeholder lesson steps and generic object labels with evidence-based steps where needed.
4. Implement dedicated renderer families: experiments; classification; plate/grouping; digestion; magnets; ruler/thermometer; motion; material sorting; particle states/phase change; separation apparatus; life cycle; conservation/recycling; Earth–Sun–Moon.
5. Save assets under exact board/grade/subject/medium/chapter/topic/step identifiers with source references and evidence status.
6. Run chapter-specific tests and capture emulator screenshots. Review all 36 mappings, with at least one screenshot per renderer family and explicit mapping tests for every topic.
7. Mark a topic complete only after source review, DB persistence, visual inspection, inline layout, and narration-sync tests pass.

Official source starting point: https://ncert.nic.in/
