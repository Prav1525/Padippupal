package com.padippupal.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class LiveLessonModuleMappingTest {
    @Test
    fun groupsSpeechByExactModuleStepMappingInCurriculumOrder() {
        val modules = listOf(
            LiveLessonModuleCandidate("module-1", "What is a magnet?", listOf("step_1")),
            LiveLessonModuleCandidate("module-2", "Magnet poles", listOf("step_2", "step_2b"))
        )
        val segments = listOf(
            LiveLessonSegmentCandidate("step_1", "A magnet attracts iron."),
            LiveLessonSegmentCandidate("step_2", "A magnet has two poles."),
            LiveLessonSegmentCandidate("step_2b", "They are called north and south.")
        )

        val grouped = groupLiveLessonSegmentsByModule(modules, segments)

        assertEquals(2, grouped?.size)
        assertEquals(listOf("module-1", "module-2"), grouped?.map { it.moduleKey })
        assertEquals("step_1", grouped?.get(0)?.stepId)
        assertEquals("step_2", grouped?.get(1)?.stepId)
        assertEquals("A magnet attracts iron.", grouped?.get(0)?.spokenText)
        assertEquals("A magnet has two poles. They are called north and south.", grouped?.get(1)?.spokenText)
    }

    @Test
    fun rejectsIncompleteMappingsInsteadOfDroppingSpokenText() {
        val modules = listOf(
            LiveLessonModuleCandidate("module-1", "First module", listOf("step_1"))
        )
        val segments = listOf(
            LiveLessonSegmentCandidate("step_1", "First explanation."),
            LiveLessonSegmentCandidate("unmapped", "This explanation must not disappear.")
        )

        assertNull(groupLiveLessonSegmentsByModule(modules, segments))
    }

    @Test
    fun skipsModulesOutsideTheSelectedTopicWithoutInventingText() {
        val modules = listOf(
            LiveLessonModuleCandidate("module-1", "Neighbouring module", listOf("step_1")),
            LiveLessonModuleCandidate("module-2", "Selected module", listOf("step_2"))
        )
        val segments = listOf(LiveLessonSegmentCandidate("step_2", "Selected topic explanation."))

        val grouped = groupLiveLessonSegmentsByModule(modules, segments)

        assertEquals(1, grouped?.size)
        assertEquals("module-2", grouped?.single()?.moduleKey)
        assertEquals("Selected topic explanation.", grouped?.single()?.spokenText)
    }
}
