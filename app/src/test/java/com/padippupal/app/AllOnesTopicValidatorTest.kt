package com.padippupal.app

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class AllOnesTopicValidatorTest {
    @Test
    fun acceptsNaturalRepeatedOnesExplanationAndShortTransition() {
        assertNull(AllOnesTopicValidator.failureReason(listOf(
            "The All 1s pattern repeats the number 1: 1, 1, 1." to
                "The All 1s pattern repeats the number 1: 1, 1, 1.",
            "Each term stays the same because the number 1 repeats." to
                "Each term stays the same because the number 1 repeats.",
            "Now look at the sequence." to "Now look at the sequence."
        )))
    }


    @Test
    fun acceptsAnApprovedTransitionWhenCaptionDuplicatesSpokenText() {
        assertNull(AllOnesTopicValidator.failureReason(listOf(
            "The All 1s pattern repeats the number 1." to
                "The All 1s pattern repeats the number 1.",
            "Now look at the sequence." to "Now look at the sequence."
        )))
    }

    @Test
    fun rejectsGenericLaterSegmentEvenWhenOpeningIsRelevant() {
        val reason = AllOnesTopicValidator.failureReason(listOf(
            "Today we will learn All 1s: 1, 1, 1." to "All 1s: 1, 1, 1.",
            "Mathematics is the search for patterns and explanations." to
                "Mathematics is the search for patterns and explanations."
        ))
        assertNotNull(reason)
        org.junit.Assert.assertTrue(reason!!.contains("segment 2"))
    }

    @Test
    fun rejectsForbiddenSquareNumberContentEvenWhenTopicIsMentioned() {
        val reason = AllOnesTopicValidator.failureReason(listOf(
            "The All 1s pattern repeats the number 1." to
                "The All 1s pattern repeats the number 1.",
            "Now let us look at square numbers." to "Now let us look at square numbers."
        ))
        assertNotNull(reason)
        org.junit.Assert.assertTrue(reason!!.contains("forbidden/off-topic"))
    }

    @Test
    fun rejectsSupportingExplanationsAsTopicSignalsWhenTopicIsNeverNamed() {
        val supportingOnlySegments = listOf(
            "A pattern can stay the same without increasing." to
                "A pattern can stay the same without increasing.",
            "A pattern can repeat without increasing or decreasing." to
                "A pattern can repeat without increasing or decreasing."
        )

        supportingOnlySegments.forEach { segment ->
            val reason = AllOnesTopicValidator.failureReason(listOf(segment))
            assertNotNull(reason)
            org.junit.Assert.assertTrue(
                "Supporting language must not count as an explicit All 1s topic signal: $segment",
                reason!!.contains("no segment explicitly identifies")
            )
        }
    }
}
