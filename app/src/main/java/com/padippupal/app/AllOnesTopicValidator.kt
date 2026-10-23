package com.padippupal.app

/**
 * Fail-closed topic check for the live tutor's All 1s lesson.
 *
 * Every segment must be relevant or a narrowly approved short transition, and at
 * least one segment must explicitly identify the repeated-one concept. Captions
 * are included because they are displayed alongside the spoken words.
 */
internal object AllOnesTopicValidator {
    private val forbidden = Regex(
        """\b(square numbers?|count(?:ing)? numbers? up and down|1\s*\+\s*2\s*\+\s*1\s*=\s*4|1\s*²)\b""",
        RegexOption.IGNORE_CASE
    )
    private val relevant = Regex(
        """(all\s+1s?|all\s+ones?|repeat(?:s|ed|ing)?\s+(?:the\s+)?(?:number\s+)?(?:1|one|ones)\b|1\s*[,;]\s*1|number one|each term is (?:the )?(?:number )?(?:1|one))""",
        RegexOption.IGNORE_CASE
    )
    private val supporting = Regex(
        """(pattern\w*.{0,70}repeat\w*|without\s+(increasing|decreasing)|(?:does|do)\s+not\s+(increase|decrease|change)|(?:doesn't|don't)\s+(increase|decrease|change)|(?:stays?|remains?)\s+(constant|unchanged|the same)|same value)""",
        RegexOption.IGNORE_CASE
    )
    private val neutralTransition = Regex(
        """^(?:now\s+)?(?:let'?s\s+)?(?:look carefully at the sequence|look at the sequence|try the next step|think about it|your turn|take a moment|tell me what you notice|what do you notice\??|pause here)[.!?\s]*$""",
        RegexOption.IGNORE_CASE
    )

    /** Returns a safe, user-displayable validation reason, or null when accepted. */
    fun failureReason(segments: List<Pair<String, String>>): String? {
        if (segments.isEmpty()) return "no lesson segments were returned"
        val textSegments = segments.map { (spoken, caption) ->
            if (caption.isBlank() || caption.equals(spoken, ignoreCase = true)) spoken.trim()
            else "$spoken $caption".trim()
        }
        val invalidSegments = textSegments.mapIndexedNotNull { index, text ->
            when {
                forbidden.containsMatchIn(text) -> "segment ${index + 1}: forbidden/off-topic content"
                !relevant.containsMatchIn(text) &&
                    !supporting.containsMatchIn(text) &&
                    !neutralTransition.matches(text) ->
                    "segment ${index + 1}: no All 1s explanation or approved short transition"
                else -> null
            }
        }
        val hasRelevantSpeech = textSegments.any { relevant.containsMatchIn(it) }
        val reasons = (invalidSegments + if (!hasRelevantSpeech) {
            listOf("no segment explicitly identifies the repeated-one topic")
        } else emptyList()).distinct()
        return reasons.takeIf { it.isNotEmpty() }?.joinToString("; ")
    }
}
