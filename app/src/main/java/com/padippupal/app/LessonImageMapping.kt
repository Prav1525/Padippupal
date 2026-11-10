package com.padippupal.app

internal data class LessonImageMappingCandidate(
    val index: Int,
    val moduleKey: String,
    val stepIds: List<String>
)

/** Return every asset mapped to the active teaching step, including paired visuals. */
internal fun matchingLessonImageIndexes(
    candidates: List<LessonImageMappingCandidate>,
    stepId: String,
    moduleKey: String
): List<Int> {
    val activeStep = stepId.trim()
    if (activeStep.isNotBlank()) {
        return candidates.filter { activeStep in it.stepIds }.map { it.index }
    }
    val activeModule = moduleKey.trim()
    if (activeModule.isBlank()) return emptyList()
    return candidates.filter { it.moduleKey == activeModule }.map { it.index }
}
