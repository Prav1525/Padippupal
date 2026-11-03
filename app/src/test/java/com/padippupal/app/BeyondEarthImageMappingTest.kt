package com.padippupal.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BeyondEarthImageMappingTest {
    private fun asset(
        id: String,
        module: String,
        vararg steps: String
    ) = BeyondEarthImageAsset(
        id = id,
        url = "/chapter-lessons/images/$id",
        title = id,
        altText = id,
        moduleKey = module,
        stepIds = steps.toSet()
    )

    @Test
    fun returnsEveryImageMappedToTheSameModule() {
        val images = listOf(
            asset("m1-a", "module-1", "step-a"),
            asset("m1-b", "module-1", "step-b"),
            asset("m1-c", "module-1", "step-c"),
            asset("m2-a", "module-2", "step-d")
        )

        val matched = matchingBeyondEarthImageAssets(images, stepId = "", moduleKey = "module-1")

        assertEquals(listOf("m1-a", "m1-b", "m1-c"), matched.map { it.id })
    }

    @Test
    fun includesStepMappedImagesAndModuleImagesWithoutDuplicates() {
        val images = listOf(
            asset("shared", "module-1", "step-a"),
            asset("module-only", "module-1", "step-b"),
            asset("step-only", "module-2", "step-a")
        )

        val matched = matchingBeyondEarthImageAssets(images, stepId = "step-a", moduleKey = "module-1")

        assertEquals(listOf("shared", "module-only", "step-only"), matched.map { it.id })
        assertEquals(3, matched.distinctBy { it.id }.size)
    }

    @Test
    fun returnsNoImagesForAnUnmappedModuleOrStep() {
        val images = listOf(asset("m1-a", "module-1", "step-a"))

        val matched = matchingBeyondEarthImageAssets(images, stepId = "missing-step", moduleKey = "module-7")

        assertTrue(matched.isEmpty())
    }

    @Test
    fun deduplicatesRepeatedAssetIds() {
        val images = listOf(
            asset("same", "module-1", "step-a"),
            asset("same", "module-1", "step-b")
        )

        val matched = matchingBeyondEarthImageAssets(images, stepId = "", moduleKey = "module-1")

        assertEquals(1, matched.size)
    }
}
