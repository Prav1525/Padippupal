package com.padippupal.app

/**
 * Pure mapping model for original textbook images attached to tutor modules/steps.
 * Kept separate from Compose UI so JVM unit tests do not initialize Android UI classes.
 */
internal data class BeyondEarthImageAsset(
    val id: String,
    val url: String,
    val title: String,
    val altText: String,
    val moduleKey: String,
    val stepIds: Set<String>
)

internal fun matchingBeyondEarthImageAssets(
    images: List<BeyondEarthImageAsset>,
    stepId: String,
    moduleKey: String
): List<BeyondEarthImageAsset> {
    return images.filter { image ->
        (stepId.isNotBlank() && stepId in image.stepIds) ||
            (moduleKey.isNotBlank() && image.moduleKey == moduleKey)
    }.distinctBy { it.id.ifBlank { it.url } }
}
