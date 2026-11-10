package com.padippupal.app

internal data class LiveLessonModuleCandidate(
    val moduleKey: String,
    val title: String,
    val stepIds: List<String>
)

internal data class LiveLessonSegmentCandidate(
    val id: String,
    val spokenText: String
)

internal data class LiveLessonModuleGroup(
    val moduleKey: String,
    val title: String,
    val stepId: String,
    val spokenText: String
)

/**
 * Group approved lesson speech by the exact module/step mapping returned by the
 * lesson-image manifest. Return null rather than silently dropping or misplacing
 * any spoken segment when the mapping is incomplete.
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
