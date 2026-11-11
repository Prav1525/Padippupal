package com.padippupal.app

internal data class LiveLessonModuleCandidate(
    val moduleKey: String,
    val title: String,
    val stepIds: List<String>
)

internal data class LiveLessonSegmentCandidate(
    val id: String,
    val spokenText: String,
    val moduleKey: String = "",
    val moduleTitle: String = ""
)

internal fun moduleCandidatesFromLessonSegments(
    segments: List<LiveLessonSegmentCandidate>
): List<LiveLessonModuleCandidate>? {
    if (segments.isEmpty()) return null
    val modulesByKey = linkedMapOf<String, LiveLessonModuleCandidate>()
    segments.forEachIndexed { index, segment ->
        val stepId = segment.id.trim()
        if (stepId.isBlank()) return null
        val stepNumber = Regex("step[_-]?([1-9][0-9]*)")
            .matchEntire(stepId)?.groupValues?.get(1)?.toIntOrNull()
        val moduleNumber = stepNumber ?: (index + 1)
        val moduleKey = segment.moduleKey.trim().ifBlank { "module-$moduleNumber" }
        val title = segment.moduleTitle.trim().ifBlank { "Module $moduleNumber" }
        val previous = modulesByKey[moduleKey]
        modulesByKey[moduleKey] = LiveLessonModuleCandidate(
            moduleKey = moduleKey,
            title = previous?.title?.takeIf { it.isNotBlank() } ?: title,
            stepIds = (previous?.stepIds.orEmpty() + stepId).distinct()
        )
    }
    return modulesByKey.values.sortedBy {
        it.moduleKey.substringAfterLast("-").toIntOrNull() ?: Int.MAX_VALUE
    }
}

internal data class LiveLessonModuleGroup(
    val moduleKey: String,
    val title: String,
    val stepId: String,
    val spokenText: String
)

/**
 * Group approved lesson speech by the module identity returned with each teaching
 * step. This source is independent of image availability: missing images must not
 * collapse the learner-facing module layout. Return null rather than dropping text.
 */
internal fun groupLiveLessonSegmentsByModule(
    modules: List<LiveLessonModuleCandidate>,
    segments: List<LiveLessonSegmentCandidate>
): List<LiveLessonModuleGroup>? {
    if (modules.isEmpty() || segments.isEmpty()) return null

    val assigned = mutableSetOf<Int>()
    val groups = mutableListOf<LiveLessonModuleGroup>()

    modules.forEach { module ->
        val moduleKey = module.moduleKey.trim()
        val title = module.title.trim()
        val stepIds = module.stepIds.map { it.trim() }.filter { it.isNotBlank() }.toSet()
        if (moduleKey.isBlank() || title.isBlank() || stepIds.isEmpty()) return null

        val matchingIndexes = segments.indices.filter { segments[it].id.trim() in stepIds }
        if (matchingIndexes.isEmpty()) return@forEach
        if (matchingIndexes.any { !assigned.add(it) }) return null

        val spokenText = matchingIndexes
            .map { segments[it].spokenText.trim() }
            .filter { it.isNotBlank() }
            .joinToString(" ")
            .trim()
        if (spokenText.isBlank()) return null

        groups += LiveLessonModuleGroup(
            moduleKey = moduleKey,
            title = title,
            stepId = segments[matchingIndexes.first()].id.trim(),
            spokenText = spokenText
        )
    }

    if (groups.isEmpty() || assigned.size != segments.size) return null
    return groups
}
