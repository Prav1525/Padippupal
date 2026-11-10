package com.padippupal.app

import org.junit.Assert.assertEquals
import org.junit.Test

class LessonImageMappingTest {
    @Test
    fun returnsBothImagesWhenAVisualUsesPairedAssetsForOneStep() {
        val candidates = listOf(
            LessonImageMappingCandidate(0, "module-4", listOf("step_4")),
            LessonImageMappingCandidate(1, "module-4", listOf("step_4")),
            LessonImageMappingCandidate(2, "module-5", listOf("step_5"))
        )

        assertEquals(
            listOf(0, 1),
            matchingLessonImageIndexes(candidates, stepId = "step_4", moduleKey = "module-4")
        )
    }

    @Test
    fun prefersExactStepMappingWhenStepIdIsAvailable() {
        val candidates = listOf(
            LessonImageMappingCandidate(0, "module-4", listOf("step_4")),
            LessonImageMappingCandidate(1, "module-4", listOf("step_5"))
        )

        assertEquals(
            listOf(0),
            matchingLessonImageIndexes(candidates, stepId = "step_4", moduleKey = "module-4")
        )
    }

    @Test
    fun fallsBackToEveryImageInTheModuleOnlyWhenStepIdIsBlank() {
        val candidates = listOf(
            LessonImageMappingCandidate(0, "module-4", listOf("step_4")),
            LessonImageMappingCandidate(1, "module-4", listOf("step_4")),
            LessonImageMappingCandidate(2, "module-5", listOf("step_5"))
        )

        assertEquals(
            listOf(0, 1),
            matchingLessonImageIndexes(candidates, stepId = "", moduleKey = "module-4")
        )
    }

    @Test
    fun returnsNoImagesForAnUnmappedStep() {
        val candidates = listOf(
            LessonImageMappingCandidate(0, "module-4", listOf("step_4"))
        )

        assertEquals(
            emptyList<Int>(),
            matchingLessonImageIndexes(candidates, stepId = "step_6", moduleKey = "module-4")
        )
    }
}
